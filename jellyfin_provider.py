"""Jellyfin audio adapter for ResonaDeck.

Converts Jellyfin's JSON audio catalog into the tiny Plex-shaped element tree
consumed by the existing ResonaDeck catalogue. No Plex authentication or
library state is modified. Network calls always go to the user's selected
Jellyfin endpoint and use the backend's aiohttp session.
"""
import datetime
import re
import urllib.parse
from typing import Any


# Injected by the backend to avoid a second metadata model drifting over time.
def _ts(s):
    if not s: return 0
    try: return int(datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp())
    except (ValueError, TypeError, OverflowError): return 0


def _image(row, kind='Primary'):
    tag = (row.get('ImageTags') or {}).get(kind)
    ident = str(row.get('Id') or '')
    if ident and tag:
        return '/Items/' + urllib.parse.quote(ident, safe='') + '/Images/' + kind + '?tag=' + urllib.parse.quote(str(tag), safe='')
    return ''


def _base_attrs(row):
    typ = str(row.get('Type') or '')
    kind = {'Audio':'track','MusicAlbum':'album','MusicArtist':'artist','AudioBook':'album','Folder':'album', 'BoxSet':'collection', 'Playlist':'playlist'}.get(typ, 'album')
    artist = str(row.get('AlbumArtist') or '') or ', '.join(row.get('Artists') or [])
    album = str(row.get('Album') or '')
    artist_ids = row.get('AlbumArtists') or row.get('ArtistItems') or []
    return {
        'ratingKey': str(row.get('Id') or ''), 'key': str(row.get('Id') or ''),
        'type': kind, 'title': str(row.get('Name') or 'Untitled'),
        'parentTitle': artist if kind == 'album' else album,
        'grandparentTitle': artist, 'originalTitle': artist,
        'parentRatingKey': str(row.get('ParentId') or row.get('AlbumId') or ''),
        'grandparentRatingKey': str((artist_ids[0] if isinstance(artist_ids[0], str) else artist_ids[0].get('Id', '')) if artist_ids else ''),
        'thumb': _image(row) or (_image({'Id': row.get('AlbumId'), 'ImageTags': {'Primary': row.get('AlbumPrimaryImageTag')}}) if row.get('AlbumPrimaryImageTag') else ''),
        'parentThumb': _image({'Id': row.get('AlbumId'), 'ImageTags': {'Primary': row.get('AlbumPrimaryImageTag')}}) if row.get('AlbumPrimaryImageTag') else '',
        'art': _image(row, 'Backdrop') or _image(row),
        'year': str(row.get('ProductionYear') or 0),
        'index': str(row.get('IndexNumber') or 0),
        'duration': str(int(row.get('RunTimeTicks') or 0)//10000),
        'leafCount': str(row.get('ChildCount') or 0), 'childCount': str(row.get('ChildCount') or 0),
        'summary': str(row.get('Overview') or ''), 'addedAt': str(_ts(row.get('DateCreated'))),
        'updatedAt': str(_ts(row.get('DateLastSaved') or row.get('DateCreated'))),
        'viewOffset': str(int((row.get('UserData') or {}).get('PlaybackPositionTicks') or 0)//10000),
        'viewCount': str((row.get('UserData') or {}).get('PlayCount') or 0),
        'lastViewedAt': str(_ts((row.get('UserData') or {}).get('LastPlayedDate'))),
        'guid': str((row.get('ProviderIds') or {}).get('MusicBrainzReleaseTrack') or ''),
    }


def to_plex(row, element):
    attrs = _base_attrs(row)
    kind = attrs['type']
    tag = 'Track' if kind == 'track' else 'Directory'
    node = element(tag, attrs)
    if kind == 'track':
        media_sources = row.get('MediaSources') or []
        src = media_sources[0] if media_sources else {}
        codec = next((s.get('Codec','') for s in src.get('MediaStreams',[]) if s.get('Type') == 'Audio'), '')
        media = element('Media', {'container': str(src.get('Container') or row.get('Container') or ''),
                  'audioCodec': str(codec or ''), 'bitrate': str(src.get('Bitrate') or 0)})
        media.children.append(element('Part', {'key': '/Audio/' + urllib.parse.quote(str(row.get('Id') or ''), safe='') + '/stream?static=true',
                              'file': str(row.get('Path') or ''), 'size': str(src.get('Size') or 0)}))
        node.children.append(media)
    return node


class JellyfinBridge:
    def __init__(self, plugin, element):
        self.p = plugin
        self.element = element

    async def get(self, route, params=None):
        base = self.p._server.base_url.rstrip('/')
        return await self.p._json('GET', base + '/' + route.lstrip('/'), token=self.p._server.access_token, params=params)

    async def plex_xml(self, path: str, params=None):
        params = dict(params or {})
        el = self.element
        uid = str(self.p._jellyfin_auth.get('userId') or '')
        if not uid: raise RuntimeError('Connect your Jellyfin user first')
        root = el('MediaContainer', {'size':'0','totalSize':'0','offset':str(params.get('X-Plex-Container-Start',0))})
        if path == '/library/sections':
            response = await self.get('Users/' + uid + '/Views')
            for row in response.get('Items',[]):
                # Only audio collections; never present video libraries as music.
                if row.get('CollectionType') not in ('music', 'books', 'audiobooks'):
                    continue
                root.children.append(el('Directory', {'key':str(row.get('Id') or ''), 'title': str(row.get('Name') or 'Music'), 'type':'artist', 'uuid':str(row.get('Id') or '')}))
            root.attrib['size'] = root.attrib['totalSize'] = str(len(root.children))
            return root
        # /library/metadata/{id}/children, /allLeaves and item details
        m = re.fullmatch(r'/library/metadata/([^/]+)(/(?:children|allLeaves))?',path)
        if m:
            ident = urllib.parse.unquote(m.group(1)); children = m.group(2)
            if not children:
                row = await self.get('Users/' + uid + '/Items/' + urllib.parse.quote(ident, safe=''))
                root.children = [to_plex(row, el)] if row.get('Id') else []
            else:
                parent = await self.get('Users/' + uid + '/Items/' + urllib.parse.quote(ident, safe=''))
                is_artist = parent.get('Type') == 'MusicArtist'
                q = {'UserId':uid, 'Recursive':'true' if children == '/allLeaves' or is_artist else 'false',
                     'IncludeItemTypes':'Audio' if children == '/allLeaves' or is_artist else 'Audio,MusicAlbum,Folder',
                     'Fields':'MediaSources,Path,DateCreated,Overview', 'Limit':1000,
                     'SortBy':'ParentIndexNumber,IndexNumber,SortName'}
                if is_artist: q['AlbumArtistIds'] = ident
                else: q['ParentId'] = ident
                rows = await self.get('Items',q)
                root.children = [to_plex(x,el) for x in rows.get('Items',[])]
                root.attrib['totalSize'] = str(rows.get('TotalRecordCount',len(root.children)))
            root.attrib['size'] = str(len(root.children))
            return root
        section = re.fullmatch(r'/library/sections/([^/]+)/(albums|all|collections|genre|recentlyAdded)',path)
        if section:
            parent, route = urllib.parse.unquote(section.group(1)), section.group(2)
            plex_type = str(params.get('type') or '')
            kind = 'Audio' if plex_type == '10' else 'MusicArtist' if plex_type == '8' else 'MusicAlbum'
            if route == 'collections': kind = 'BoxSet'
            if route == 'genre':
                data = await self.get('Genres', {'UserId':uid,'ParentId':parent,'Limit':500})
                root.children = [el('Directory', {'key':str(x.get('Id') or ''),'title':str(x.get('Name') or ''),'type':'genre'}) for x in data.get('Items',[])]
                root.attrib['size'] = root.attrib['totalSize'] = str(len(root.children))
                return root
            start,limit = int(params.get('X-Plex-Container-Start',0)), int(params.get('X-Plex-Container-Size',100))
            q = {'UserId':uid,'ParentId':parent,'Recursive':'true','IncludeItemTypes':kind,
                 'StartIndex':start,'Limit':limit,'Fields':'MediaSources,Path,DateCreated,Overview',
                 'SortBy':'SortName', 'SortOrder':'Ascending'}
            if route == 'albums' and kind == 'MusicAlbum': pass
            if params.get('title'): q['SearchTerm'] = params['title']
            if 'addedAt:desc' in str(params.get('sort') or ''): q.update({'SortBy':'DateCreated','SortOrder':'Descending'})
            if 'lastViewedAt' in str(params.get('sort') or ''): q.update({'SortBy':'DatePlayed','SortOrder':'Descending'})
            data = await self.get('Items',q)
            root.children = [to_plex(x,el) for x in data.get('Items',[])]
            root.attrib.update({'size':str(len(root.children)),'totalSize':str(data.get('TotalRecordCount',len(root.children))),'offset':str(start)})
            return root
        if path.startswith('/hubs') or path.startswith('/playlists'):
            return root
        raise RuntimeError('Jellyfin adapter does not support: ' + path.split('?')[0][:130])
