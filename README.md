# 🎬 Movie Shorts Maker (올인원 쇼츠 메이커)

유튜브 **'잡학다식 개발자'** 채널에서 소개하는, 영화 정보를 기반으로 유튜브 쇼츠(Shorts) 영상을 자동으로 기획하고 생성해 주는 파이썬 자동화 프로그램입니다.

## ✨ 주요 기능 (Key Features)

* **영화 검색 및 랜덤 픽:** 원하는 영화 제목을 직접 검색하거나, 랜덤 버튼을 통해 예상치 못한 명작을 쇼츠 주제로 간편하게 선정할 수 있습니다.
* **자동화된 영상 소스 수집:** `yt_dlp` 라이브러리를 활용하여 쇼츠 제작에 필요한 영상 소스를 빠르고 안정적으로 다운로드합니다.
* **원클릭 쇼츠(9:16) 생성:** 번거로운 편집 과정 없이, 단일 UI 화면에서 '만들기' 버튼 한 번으로 쇼츠 규격에 최적화된 결과물을 뚝딱 만들어냅니다.
* **사용자 행동 트래킹:** Supabase 데이터베이스와 연동하여 실시간 사용량과 인기 검색 영화 데이터를 수집, 향후 콘텐츠 기획에 활용합니다.

## 🚀 설치 및 실행 방법 (Getting Started)

이 프로젝트는 최신 파이썬 패키지 관리자인 `uv` 환경에 최적화되어 있습니다. (Python 3.10 이상 권장)

### 1. 저장소 복제 (Clone)
```bash
git clone [https://github.com/gohard-lab/movie_shorts_maker.git](https://github.com/gohard-lab/movie_shorts_maker.git)
cd movie_shorts_maker
```

### 2. 의존성 패키지 설치
pyproject.toml을 기반으로 필요한 라이브러리(yt_dlp 등)를 한 번에 설치합니다.

```Bash
uv sync
```

### 3. 프로그램 실행
```Bash
uv run python all_in_one_shorts.py
```

*(실행 파일(.exe) 버전이 필요하신 경우, uv run pyinstaller -F -w all_in_one_shorts.py 명령어를 통해 직접 빌드하실 수 있습니다.)*

### 📊 데이터 수집 안내
본 프로그램은 더 나은 서비스 제공과 에러 수정을 위해 익명화된 최소한의 사용 통계(기능 클릭 수 등)를 수집합니다. 수집되는 데이터는 '검색/랜덤 방식 여부' 및 '선택된 영화명'으로 한정되며, 개인을 특정할 수 있는 정보는 일절 수집하지 않습니다.

### 👨‍💻 제작자 및 관련 링크 (Creator)
GitHub: @gohard-lab

YouTube: 잡학다식 개발자 채널 바로가기

상세 작동 원리 및 코딩 과정: 유튜브 영상과 커뮤니티 게시글을 참고해 주세요.

[https://youtu.be/3m4AEVO1swg](https://youtu.be/3m4AEVO1swg)