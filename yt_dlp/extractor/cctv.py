import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    try_get,
    unified_timestamp,
    url_or_none,
)


# Updated by: tekintian@gmail.com
class CCTVIE(InfoExtractor):
    IE_DESC = '央视网'
    # 优先级：CCTVListIE 处理列表页面，CCTVIE 处理单个视频
    # 列表页面格式：tv.cctv.com/YYYY/MM/DD/VIDALxxx.shtml 或 tv.cctv.com/YYYY/MM/DD/VIDAxxx.shtml
    # 单个视频格式：tv.cctv.com/YYYY/MM/DD/VIDEExxx.shtml
    _VALID_URL = r'https?://(?:(?:[^/]+)\.(?:cntv|cctv)\.(?:com|cn)|(?:www\.)?ncpa-classic\.com)/(?:[^/]+/)*?(?P<id>[^/?#&]+?)(?:/index)?(?:\.s?html|[?#&]|$)'

    # 排除列表页面的 URL 模式，让 CCTVListIE 优先处理
    @classmethod
    def suitable(cls, url):
        # 列表页面特征：tv.cctv.com/YYYY/MM/DD/VIDAL 或 VIDA 开头
        if re.match(r'https?://(?:tv\.cctv\.com|tv\.cntv\.cn)/\d{4}/\d{2}/\d{2}/(?:VIDAL|VIDA)', url):
            return False
        return super(CCTVIE, cls).suitable(url)
    _TESTS = [{
        # fo.addVariable("videoCenterId","id")
        'url': 'http://sports.cntv.cn/2016/02/12/ARTIaBRxv4rTT1yWf1frW2wi160212.shtml',
        'md5': 'd61ec00a493e09da810bf406a078f691',
        'info_dict': {
            'id': '5ecdbeab623f4973b40ff25f18b174e8',
            'ext': 'mp4',
            'title': '[NBA]二少联手砍下46分 雷霆主场击败鹈鹕（快讯）',
            'description': 'md5:7e14a5328dc5eb3d1cd6afbbe0574e95',
            'duration': 98,
            'uploader': 'songjunjie',
            'timestamp': 1455279956,
            'upload_date': '20160212',
        },
    }, {
        # var guid = "id"
        'url': 'http://tv.cctv.com/2016/02/05/VIDEUS7apq3lKrHG9Dncm03B160205.shtml',
        'info_dict': {
            'id': 'efc5d49e5b3b4ab2b34f3a502b73d3ae',
            'ext': 'mp4',
            'title': '[赛车] "车王"舒马赫恢复情况成谜（快讯）',
            'description': '2月4日，蒙特泽莫罗透露了关于"车王"舒马赫恢复情况，但情况是否属实遭到了质疑。',
            'duration': 37,
            'uploader': 'shujun',
            'timestamp': 1454677291,
            'upload_date': '20160205',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # changePlayer('id')
        'url': 'http://english.cntv.cn/special/four_comprehensives/index.shtml',
        'info_dict': {
            'id': '4bb9bb4db7a6471ba85fdeda5af0381e',
            'ext': 'mp4',
            'title': 'NHnews008 ANNUAL POLITICAL SEASON',
            'description': 'Four Comprehensives',
            'duration': 60,
            'uploader': 'zhangyunlei',
            'timestamp': 1425385521,
            'upload_date': '20150303',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # loadvideo('id')
        'url': 'http://cctv.cntv.cn/lm/tvseries_russian/yilugesanghua/index.shtml',
        'info_dict': {
            'id': 'b15f009ff45c43968b9af583fc2e04b2',
            'ext': 'mp4',
            'title': 'Путь，усыпанный космеями Серия 1',
            'description': 'Путь, усыпанный космеями',
            'duration': 2645,
            'uploader': 'renxue',
            'timestamp': 1477479241,
            'upload_date': '20161026',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # var initMyAray = 'id'
        'url': 'http://www.ncpa-classic.com/2013/05/22/VIDE1369219508996867.shtml',
        'info_dict': {
            'id': 'a194cfa7f18c426b823d876668325946',
            'ext': 'mp4',
            'title': '小泽征尔音乐塾 音乐梦想无国界',
            'duration': 2173,
            'timestamp': 1369248264,
            'upload_date': '20130522',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # videoCenterId: "id"
        'url': 'http://news.cctv.com/2024/02/21/ARTIcU5tKIOIF2myEGCATkLo240221.shtml',
        'info_dict': {
            'id': '5c846c0518444308ba32c4159df3b3e0',
            'ext': 'mp4',
            'title': '《平"语"近人——习近平喜欢的典故》第三季 第5集：风物长宜放眼量',
            'uploader': 'yangjuan',
            'timestamp': 1708554940,
            'upload_date': '20240221',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # var ids = ["id"]
        'url': 'http://www.ncpa-classic.com/clt/more/416/index.shtml',
        'info_dict': {
            'id': 'a8606119a4884588a79d81c02abecc16',
            'ext': 'mp3',
            'title': '来自维也纳的新年贺礼',
            'description': 'md5:f13764ae8dd484e84dd4b39d5bcba2a7',
            'duration': 1578,
            'uploader': 'djy',
            'timestamp': 1482942419,
            'upload_date': '20161228',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        'url': 'http://ent.cntv.cn/2016/01/18/ARTIjprSSJH8DryTVr5Bx8Wb160118.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cntv.cn/video/C39296/e0210d949f113ddfb38d31f00a4e5c44',
        'only_matching': True,
    }, {
        'url': 'http://english.cntv.cn/2016/09/03/VIDEhnkB5y9AgHyIEVphCEz1160903.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cctv.com/2016/09/07/VIDE5C1FnlX5bUywlrjhxXOV160907.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cntv.cn/video/C39296/95cfac44cabd3ddc4a9438780a4e5c44',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            [r'var\s+guid\s*=\s*["\']([\da-fA-F]+)',
             r'videoCenterId(?:["\']\s*,|:)\s*["\']([\da-fA-F]+)',
             r'changePlayer\s*\(\s*["\']([\da-fA-F]+)',
             r'load[Vv]ideo\s*\(\s*["\']([\da-fA-F]+)',
             r'var\s+initMyAray\s*=\s*["\']([\da-fA-F]+)',
             r'var\s+ids\s*=\s*\[["\']([\da-fA-F]+)'],
            webpage, 'video id')

        data = self._download_json(
            'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do', video_id,
            query={
                'pid': video_id,
                'url': url,
                'idl': 32,
                'idlr': 32,
                'modifyed': 'false',
            })

        title = data['title']

        formats = []

        video = data.get('video')
        if isinstance(video, dict):
            for quality, chapters_key in enumerate(('lowChapters', 'chapters')):
                video_url = try_get(
                    video, lambda x: x[chapters_key][0]['url'], str)
                if video_url:
                    formats.append({
                        'url': video_url,
                        'format_id': 'http',
                        'quality': quality,
                        # Sample clip
                        'preference': -10,
                    })

        hls_url = try_get(data, lambda x: x['hls_url'], str)
        if hls_url:
            hls_url = re.sub(r'maxbr=\d+&?', '', hls_url)
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False))

        uploader = data.get('editer_name')
        description = self._html_search_meta(
            'description', webpage, default=None)
        timestamp = unified_timestamp(data.get('f_pgmtime'))
        duration = float_or_none(try_get(video, lambda x: x['totalLength']))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }


# Updated by: tekintian@gmail.com
class CCTVListIE(InfoExtractor):
    """
    CCTV 视频列表页面提取器

    支持提取 CCTV 网站上的视频列表页面，批量下载列表中的所有视频。

    支持的 URL 格式：
    - https://tv.cctv.com/2016/12/28/VIDALOmjxOZe51NjntPvOI00161228.shtml
    - https://tv.cntv.cn/2020/05/18/VIDA3AlxjIBhKl2DxKrrz4HQ200518.shtml

    Updated by: tekintian@gmail.com
    """
    IE_DESC = '央视网列表'
    _VALID_URL = r'https?://(?:tv\.cctv\.com|tv\.cntv\.cn)/\d{4}/\d{2}/\d{2}/(?P<id>(?:VIDAL|VIDA)[^/]+)\.shtml'

    _TESTS = [{
        'url': 'https://tv.cctv.com/2016/12/28/VIDALOmjxOZe51NjntPvOI00161228.shtml',
        'info_dict': {
            'id': 'VIDALOmjxOZe51NjntPvOI00161228',
            'title': str,
            'description': str,
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://tv.cctv.com/2020/05/18/VIDA3AlxjIBhKl2DxKrrz4HQ200518.shtml',
        'info_dict': {
            'id': 'VIDA3AlxjIBhKl2DxKrrz4HQ200518',
            'title': str,
        },
        'playlist_mincount': 5,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id, note='Downloading playlist page')

        # 提取页面标题
        title = self._html_search_meta('title', webpage, 'title', default=None) or self._og_search_title(webpage)
        description = self._html_search_meta('description', webpage, 'description', default=None)

        # 提取页面封面图
        thumbnail = self._html_search_regex(
            [r'flvImgUrl\s*=\s*"([^"]+)"',
             r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
             r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']'],
            webpage, 'thumbnail', default=None)
        if thumbnail and thumbnail.startswith('//'):
            thumbnail = 'https:' + thumbnail

        # 方法1: 从页面中的 jsonData 变量提取视频列表（优先）
        entries = self._extract_from_jsondata(webpage, url, thumbnail)

        # 方法2: 如果方法1失败，从 HTML 中直接提取视频链接（备用）
        if not entries:
            entries = self._extract_from_html(webpage, url, thumbnail)

        if not entries:
            raise ExtractorError('No videos found on this page')

        return self.playlist_result(entries, playlist_id, playlist_title=title, playlist_description=description)

    def _extract_from_jsondata(self, webpage, url, default_thumbnail):
        """从页面 JavaScript 变量 jsonData 中提取视频列表"""
        # 查找 jsonData 变量
        json_data_match = self._search_regex(
            r'var\s+jsonData\d+\s*=\s*(\[[\s\S]*?\]);',
            webpage, 'json data', default=None)

        if not json_data_match:
            return []

        try:
            import json
            video_list = json.loads(json_data_match)
        except Exception:
            return []

        entries = []
        for video in video_list:
            video_url = video.get('url')
            if not video_url or not url_or_none(video_url):
                continue

            # 提取视频标题
            video_title = video.get('title') or video.get('brief')
            if not video_title:
                continue

            # 提取封面图
            image = video.get('img')
            if image:
                if image.startswith('//'):
                    image = 'https:' + image
            else:
                image = default_thumbnail

            # 提取时长
            length = video.get('length', '')

            entries.append({
                '_type': 'url',
                'url': video_url,
                'title': video_title,
                'thumbnail': image,
                'duration': self._parse_duration(length),
            })

        return entries

    def _extract_from_html(self, webpage, url, default_thumbnail):
        """从 HTML 中提取视频链接（备用方法）"""
        # 查找所有视频链接
        video_links = re.findall(
            r'href="(https?://(?:tv\.cctv\.com|tv\.cntv\.cn)/[^"]*VIDE\w+\.shtml)"',
            webpage)

        # 去重
        video_links = list(dict.fromkeys(video_links))

        if not video_links:
            return []

        entries = []
        for video_url in video_links:
            # 尝试从周围的 HTML 中提取标题
            link_pattern = re.escape(video_url)
            link_match = re.search(
                rf'<a[^>]*href="{link_pattern}"[^>]*title="([^"]+)"',
                webpage)
            if link_match:
                video_title = link_match.group(1)
            else:
                # 如果没有 title 属性，尝试提取链接文本
                text_match = re.search(
                    rf'<a[^>]*href="{link_pattern}"[^>]*>([^<]+)</a>',
                    webpage)
                video_title = text_match.group(1).strip() if text_match else video_url

            entries.append({
                '_type': 'url',
                'url': video_url,
                'title': video_title,
                'thumbnail': default_thumbnail,
            })

        return entries

    @staticmethod
    def _parse_duration(duration_str):
        """解析时长字符串（如 '00:28:50'）为秒数"""
        if not duration_str:
            return None

        try:
            parts = duration_str.strip().split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
        except (ValueError, TypeError):
            pass

        return None
