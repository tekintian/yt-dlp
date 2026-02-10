# yt-dlp 开发指引

## 目录

1. [项目概述](#项目概述)
2. [开发环境设置](#开发环境设置)
3. [项目结构](#项目结构)
4. [开发工作流](#开发工作流)
5. [提取器开发指南](#提取器开发指南)
6. [代码规范](#代码规范)
7. [测试指南](#测试指南)
8. [构建发布](#构建发布)
9. [常见问题](#常见问题)

---

## 项目概述

yt-dlp 是一个功能强大的命令行音视频下载器，支持从 1000+ 个网站下载媒体内容。它是 youtube-dl 的一个活跃分支，具有更多功能和持续更新。

### 核心特性

- 支持海量视频网站（YouTube, Bilibili, 央视网等）
- 支持多种格式和质量
- 下载速度控制和断点续传
- 字幕下载和字幕合并
- 元数据提取
- 播放列表批量下载

### 技术栈

- **Python**: >= 3.10 (CPython, PyPy)
- **构建工具**: Hatch, hatchling
- **测试框架**: pytest
- **代码检查**: ruff, autopep8

---

## 开发环境设置

### 推荐方式：使用 Hatch

yt-dlp 使用 `hatch` 作为项目管理工具：

安装pipx: 如果已经安装,直接跳过这一步
```bash
python -m pip install pipx
```


- 安装 hatch
官方发布的1.16.3版本有问题, 需要直接使用pipx直接安装开发版本:
~~~bash
git clone https://github.com/tekintian/hatch.git
pipx install -e ./hatch
~~~



hatch的安装可以参考[hatch的官方文档](https://hatch.pypa.io/latest/install/)


- 创建开发环境并安装依赖：
```bash
# 创建开发环境
hatch env create

# 进入开发环境
hatch shell
```

### 备选方式：手动虚拟环境

```bash
# 安装开发依赖
python -m pip install -e ".[default,dev]"

# 设置 pre-commit hook
pre-commit install
```

### 依赖安装

| 依赖类型 | 安装命令 |
|---------|---------|
| 基础依赖 | `python -m pip install -e .` |
| 开发依赖 | `python -m pip install -e ".[default,dev]"` |
| PyInstaller | `python -m pip install -e ".[pyinstaller]"` |

---

## 项目结构

```
yt-dlp/
├── yt_dlp/                    # 主包目录
│   ├── __init__.py           # 包入口
│   ├── __main__.py           # 命令行入口
│   ├── YoutubeDL.py          # 核心 YoutubeDL 类
│   ├── options.py            # 命令行选项解析
│   ├── extractor/            # 提取器模块
│   │   ├── common.py         # InfoExtractor 基类
│   │   ├── _extractors.py    # 提取器注册
│   │   ├── bilibili.py       # Bilibili 提取器示例
│   │   ├── cctv.py           # CCTV 提取器示例
│   │   └── ...               # 其他站点提取器
│   ├── downloader/          # 下载器模块
│   ├── postprocessor/        # 后处理器模块
│   └── utils/                # 工具函数
├── devscripts/               # 开发脚本
│   ├── make_lazy_extractors.py  # 生成懒加载提取器
│   └── ...
├── test/                     # 测试目录
│   ├── test_download.py      # 下载测试
│   └── ...
├── Makefile                  # 构建脚本
├── pyproject.toml            # 项目配置
└── README.md                 # 项目说明
```

---

## 开发工作流

### 1. 代码格式化和检查

```bash
# 自动修复格式问题
hatch fmt

# 或手动执行
ruff check --fix .
autopep8 --in-place .

# 仅检查不修复
hatch fmt --check
```

### 2. 运行测试

```bash
# 运行所有测试
hatch test

# 运行特定提取器测试
hatch test CCTV

# 运行离线测试（不下载）
python -m pytest -Werror -m "not download"
```

### 3. 提交代码

```bash
# 添加修改
git add <files>

# 提交
git commit -m '[extractor] Add description'

# 推送
git push origin <branch>
```

---

## 提取器开发指南

### 提取器类型

1. **InfoExtractor**: 单个视频提取器
2. **SearchInfoExtractor**: 搜索提取器
3. **InfoExtractor 派生**: 播放列表提取器（使用 `playlist_result` 返回）

### 基础模板

#### 单视频提取器

```python
from .common import InfoExtractor

class YourExtractorIE(InfoExtractor):
    IE_DESC = '站点描述'
    _VALID_URL = r'https?://(?:www\.)?example\.com/watch/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'https://example.com/watch/42',
        'md5': 'md5 of first 10241 bytes',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video Title',
            'description': 'Video description',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # 提取信息
        title = self._html_search_regex(r'<h1>([^<]+)</h1>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<',
                                           webpage, 'uploader', fatal=False),
        }
```

#### 播放列表提取器

```python
from .common import InfoExtractor

class YourPlaylistIE(InfoExtractor):
    IE_DESC = '站点播放列表'
    _VALID_URL = r'https?://(?:www\.)?example\.com/playlist/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'https://example.com/playlist/42',
        'info_dict': {
            'id': '42',
            'title': 'Playlist Title',
        },
        'playlist_mincount': 5,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        # 提取播放列表信息
        title = self._html_search_meta('title', webpage, 'title')

        # 提取视频条目
        entries = []
        for video_url in re.findall(r'href="(/watch/[^"]+)"', webpage):
            entries.append({
                '_type': 'url',
                'url': 'https://example.com' + video_url,
            })

        return self.playlist_result(entries, playlist_id, playlist_title=title)
```

### URL 路由和优先级

当多个提取器匹配同一 URL 时，可以使用 `suitable()` 方法控制路由：

```python
class VideoIE(InfoExtractor):
    _VALID_URL = r'https?://example\.com/(?P<id>[^/]+)'

    @classmethod
    def suitable(cls, url):
        # 排除播放列表 URL，让 PlaylistIE 处理
        if re.match(r'https?://example\.com/playlist/', url):
            return False
        return super(VideoIE, cls).suitable(url)
```

### 注册提取器

在 `yt_dlp/extractor/_extractors.py` 中添加导入：

```python
from .yourextractor import YourExtractorIE, YourPlaylistIE
```

---

## 代码规范

### 必需字段

```python
{
    'id': 'video_id',      # 必须
    'url': 'video_url',    # 或 'formats'
}
```

### 可选字段

```python
{
    'title': 'title',
    'description': 'description',
    'uploader': 'uploader',
    'timestamp': 1234567890,
    'duration': 3600,
    'thumbnail': 'url',
    'view_count': 1000,
    # ... 更多字段见 InfoExtractor 文档
}
```

### 安全提取原则

#### 1. 使用 `traverse_obj` 和 `fatal=False`

```python
# ✅ 正确
title = traverse_obj(data, ('video', 'title'))
description = self._search_regex(r'<span[^>]*>([^<]+)</span>',
                                webpage, 'description', fatal=False)

# ❌ 错误
title = data['video']['title']
```

#### 2. 提供多种备选方案

```python
title = (traverse_obj(data, ('video', 'title'))
         or self._og_search_title(webpage)
         or self._html_search_meta('title', webpage))
```

#### 3. 使用便利函数

```python
# 数字转换
view_count = int_or_none(data.get('views'))
duration = float_or_none(data.get('duration'), scale=1000)

# 日期时间
timestamp = unified_timestamp(data.get('created_at'))

# URL 验证
url = url_or_none(data.get('video_url'))
```

### 正则表达式规范

#### 1. 避免不必要的捕获组

```python
# ✅ 正确
r'(?:id|ID)=(?P<id>\d+)'

# ❌ 错误
r'(id|ID)=(?P<id>\d+)'
```

#### 2. 保持灵活和宽松

```python
# ✅ 正确
r'<span[^>]+class="title"[^>]*>([^<]+)'

# ❌ 错误
r'<span style="position: absolute;" class="title">(.*?)</span>'
```

#### 3. 使用命名捕获组

```python
_VALID_URL = r'https?://example\.com/(?P<id>[^/]+)'
video_id = self._match_id(url)  # 直接获取 id 组
```

### 代码风格

- **引号**: 字符串使用单引号，文档字符串使用双引号
- **行长**: 软限制 100 字符
- **缩进**: 4 空格
- **尾随括号**: 放在最后一行

```python
# ✅ 正确
url = traverse_obj(info, ('context', 'dispatcher', 'stores', 'url'), list)

# ✅ 正确
f = {
    'url': url,
    'format_id': format_id,
}

# ❌ 错误
f = {'url': url,
     'format_id': format_id}
```

---

## 测试指南

### 测试用例编写

每个提取器至少需要一个测试用例：

```python
_TESTS = [{
    'url': 'https://example.com/watch/42',
    'md5': 'TODO: md5 sum of first 10241 bytes',
    'info_dict': {
        'id': '42',
        'ext': 'mp4',
        'title': 'Video Title',
        'uploader': 'Uploader Name',
        'upload_date': '20240101',
    },
}, {
    'url': 'https://example.com/watch/other',
    'only_matching': True,  # 仅测试 URL 匹配
}, {
    'url': 'https://example.com/watch/protected',
    'skip': 'Requires login',  # 跳过原因
}]
```

### 运行测试

```bash
# 运行特定提取器
hatch test YourExtractor

# 运行所有提取器测试
hatch test all

# 查看测试输出
hatch test YourExtractor --verbose
```

### 获取测试数据

```bash
# 运行测试获取缺失字段
yt-dlp --test "https://example.com/watch/42"

# 输出将显示缺失或不正确的字段
```

---

## 构建发布

### 创建可执行文件

#### 使用 Makefile

```bash
# 基础构建
make

# 包含额外功能（如 curl-cffi）
make yt-dlp-extra

# 清理构建文件
make clean
```

#### 使用 PyInstaller

```bash
# 安装依赖
pip install -e ".[pyinstaller]"

# 构建
python -m PyInstaller --onefile --name yt-dlp yt_dlp/__main__.py
```

### 创建安装包

```bash
# 源码分发包
python -m build -sn .

# 完整分发包
python -m build
```

### 系统安装

```bash
# 使用 Makefile 安装
sudo make install

# 或使用 pip 安装
pip install .
```

---

## 常见问题

### Q: 提取器 URL 匹配冲突？

**A**: 使用 `suitable()` 方法控制路由优先级。

```python
@classmethod
def suitable(cls, url):
    if 'playlist' in url:
        return False
    return super(YourIE, cls).suitable(url)
```

### Q: 如何处理需要登录的网站？

**A**: 实现 `_perform_login()` 方法，或在测试中使用 `test/local_parameters.json`：

```json
{
    "username": "your user name",
    "password": "your password"
}
```

### Q: 如何提取加密/混淆的 JavaScript？

**A**: 使用 yt-dlp 内置的 JS 解释器或 `js_to_json` 工具函数。

```python
from ..utils import js_to_json

js_code = 'var data = {"key": "value"};'
json_data = js_to_json(js_code)
```

### Q: 播放列表很大，如何高效处理？

**A**: 使用 `OnDemandPagedList` 或 `InAdvancePagedList`：

```python
from ..utils import OnDemandPagedList

def _entries(self, playlist_id):
    for page in range(1, 100):
        yield from self._get_page_entries(page)

entries = OnDemandPagedList(
    lambda page: self._get_page_entries(page),
    lambda page: page < 100
)
return self.playlist_result(entries, playlist_id)
```

### Q: 如何调试提取器？

**A**: 使用 `--write-pages` 和 `-v` 参数：

```bash
yt-dlp -v --write-pages "https://example.com/watch/42"
# 这会保存 .dump 文件供分析
```

### Q: 如何处理年龄限制？

**A**: 在 info_dict 中设置 `age_limit` 字段：

```python
return {
    'id': video_id,
    'title': title,
    'age_limit': 18,  # 18+ 内容
}
```

---

## 参考资源

- [官方 GitHub](https://github.com/yt-dlp/yt-dlp)
- [官方 README](README.md)
- [贡献指南](CONTRIBUTING.md)
- [InfoExtractor 源码](yt_dlp/extractor/common.py)
- [示例提取器](yt_dlp/extractor/)

---

## 附录：常用工具函数

### URL 处理

```python
from ..utils import url_or_none, urljoin, base_url

url = url_or_none(raw_url)  # 验证 URL
full_url = urljoin(base, path)  # 拼接 URL
base = base_url(full_url)  # 获取基础 URL
```

### 数据解析

```python
from ..utils import (
    int_or_none, float_or_none,
    parse_count, parse_duration,
    parse_resolution, parse_iso8601,
)

count = int_or_none(view_str)
duration = parse_duration('01:23:45')
resolution = parse_resolution('1920x1080')
```

### HTML/XML 解析

```python
from ..utils import (
    clean_html, extract_attributes,
    xpath_element, xpath_text,
)

# 清理 HTML
title = clean_html(raw_html)

# 提取属性
attrs = extract_attributes('<div id="main" class="container">')
```

### 数据遍历

```python
from ..utils import traverse_obj, try_call

# 深度遍历嵌套对象
title = traverse_obj(data, ('video', 'title'), ('meta', 'og:title'))

# 安全调用函数
result = try_call(int, ['invalid'])  # 返回 None 而不是抛出异常
```

---

*最后更新: 2025-02-10*
