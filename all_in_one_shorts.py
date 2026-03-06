import sys
import os
import random
import requests
import time
import datetime
import shutil
import gc
import ctypes
import yt_dlp

from dotenv import load_dotenv

# .env 파일을 찾아서 엽니다.
load_dotenv()

# 금고 안에서 TMDB_API_KEY 라는 이름표가 붙은 진짜 키를 꺼내옵니다.
tmdb_key = os.environ.get("TMDB_API_KEY")

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, 
                             QRadioButton, QButtonGroup, QMessageBox, QGroupBox, QGridLayout, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings

from moviepy import (
    VideoFileClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips,
    TextClip, ImageClip, ColorClip
)

# ==============================================================================
# [환경 설정] - 이제 OpenAI API 키가 필요 없습니다! 무료로 즐기세요!
# ==============================================================================
TMDB_API_KEY = tmdb_key
FONT_PATH = "C:/Windows/Fonts/malgunbd.ttf"
BASE_OUTPUT_FOLDER = "outputs"
TEMP_FOLDER = "temp_batch"
TARGET_WIDTH = 720
TARGET_HEIGHT = 1280
SHORTS_DURATION = 45.0 # 숏츠 고정 길이 (45초)

GENRE_MAP = {
    "액션": 28, "SF": 878, "로맨스": 10749, "코미디": 35, 
    "공포": 27, "스릴러": 53, "판타지": 14, "애니메이션": 16, 
    "범죄": 80, "미스터리": 9648, "가족": 10751, "전쟁": 10752
}

# ==============================================================================
# [TMDB API 로직]
# ==============================================================================
def get_random_movie(genre_id):
    page = random.randint(1, 5)
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}&language=ko-KR&sort_by=popularity.desc&page={page}"
    try:
        res = requests.get(url).json()
        movies = res.get('results', [])
        if movies:
            selected = random.choice(movies)
            return {
                'id': selected.get('id'), 'media_type': 'movie', 'title': selected.get('title')
            }
    except: pass
    return None

def get_manual_movie(title):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={title}&language=ko-KR"
    try:
        res = requests.get(url).json()
        valid = [r for r in res.get('results', []) if r.get('media_type') in ['movie', 'tv']]
        if valid:
            item = valid[0]
            return {
                'id': item.get('id'), 'media_type': item.get('media_type'), 'title': item.get('title', item.get('name'))
            }
    except: pass
    return None

def download_images(movie_id, media_type='movie'):
    img_dir = os.path.join(TEMP_FOLDER, "images")
    os.makedirs(img_dir, exist_ok=True)
    url = f"https://api.themoviedb.org/3/{media_type}/{movie_id}/images?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        images = data.get('backdrops', [])[:3] + data.get('posters', [])[:2]
        downloaded = []
        for i, img in enumerate(images):
            img_url = f"https://image.tmdb.org/t/p/original{img['file_path']}"
            save_path = os.path.join(img_dir, f"img_{i}.jpg")
            with open(save_path, 'wb') as f: f.write(requests.get(img_url).content)
            downloaded.append(save_path)
        return downloaded
    except: return []

class KoreanLineEdit(QLineEdit):
    def focusInEvent(self, e):
        super().focusInEvent(e)
        try:
            hwnd = int(self.winId())
            imm32 = ctypes.windll.imm32
            h_imc = imm32.ImmGetContext(hwnd)
            if h_imc:
                imm32.ImmSetOpenStatus(h_imc, True)
                imm32.ImmSetConversionStatus(h_imc, 0x01, 0)
                imm32.ImmReleaseContext(hwnd, h_imc)
        except: pass

# ==============================================================================
# [로직] 메인 렌더링 스레드 (100% 무료 버전)
# ==============================================================================
class VideoMakerThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finish_signal = pyqtSignal(str)

    def __init__(self, movie_info):
        super().__init__()
        self.movie_info = movie_info 
        self._is_running = True 

    def stop(self):
        self._is_running = False 

    def log(self, text):
        self.log_signal.emit(text)

    def check_stop(self):
        if not self._is_running:
            self.log("🧹 내부 임시 파일을 안전하게 삭제하고 있습니다...")
            return True
        return False

    def run(self):
        start_time = time.time()
        try:
            if os.path.exists(TEMP_FOLDER):
                shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
                time.sleep(0.5)
            os.makedirs(TEMP_FOLDER, exist_ok=True)

            title = self.movie_info['title']
            self.progress_signal.emit(10)
            self.log(f"🎬 [{title}] 예고편 몽타주 숏츠 제작을 시작합니다!")
            
            if self.check_stop(): self.finish_signal.emit("중지됨|0"); return

            # 1. 다중 비주얼 소스 수집
            self.progress_signal.emit(20)
            self.log("🎥 유튜브에서 고화질 예고편 소스를 수집 중입니다...")
            
            downloaded_videos = []
            max_videos = 3 
            search_queries = [f"영화 {title} 공식 예고편", f"영화 {title} 티저", f"영화 {title} 리뷰"]
            
            ydl_opts = {'format': '18/best[ext=mp4]', 'quiet': True, 'noplaylist': True, 'overwrites': True}
            
            for query in search_queries:
                if len(downloaded_videos) >= max_videos or not self._is_running: break
                try:
                    with yt_dlp.YoutubeDL({'quiet':True, 'extract_flat': True, 'noplaylist': True}) as ydl:
                        res = ydl.extract_info(f"ytsearch3:{query}", download=False)
                        if res and 'entries' in res:
                            for entry in res['entries']:
                                if entry.get('url'):
                                    vid_idx = len(downloaded_videos) + 1
                                    out_path = os.path.join(TEMP_FOLDER, f"vid_{vid_idx}.mp4")
                                    ydl_opts['outtmpl'] = out_path
                                    try:
                                        with yt_dlp.YoutubeDL(ydl_opts) as ydl_down:
                                            ydl_down.download([entry['url']])
                                        downloaded_videos.append(out_path)
                                        self.log(f"   ✅ 영상 소스 {vid_idx} 확보 완료!")
                                        break # 하나 성공하면 다음 검색어로
                                    except: continue
                except: pass

            if self.check_stop(): self.finish_signal.emit("중지됨|0"); return

            self.progress_signal.emit(40)
            self.log("🖼️ 고화질 영화 스틸컷 이미지를 가져옵니다...")
            imgs = []
            img_files = download_images(self.movie_info['id'], self.movie_info['media_type'])
            for p in img_files:
                try: imgs.append(ImageClip(p))
                except: pass

            if self.check_stop(): self.finish_signal.emit("중지됨|0"); return

            # 2. 영상 클립 불러오기 및 오디오 추출
            self.progress_signal.emit(50)
            self.log("✂️ 수집된 소스들을 역동적으로 교차 편집합니다...")
            
            vid_clips = []
            master_audio = None # 예고편 오디오를 숏츠 배경음악으로 사용!

            for v_path in downloaded_videos:
                if os.path.exists(v_path):
                    try: 
                        c = VideoFileClip(v_path)
                        if c.duration >= 3.0:
                            if master_audio is None and c.audio is not None:
                                master_audio = c.audio # 첫 번째 영상의 오디오를 마스터로 씁니다.
                            vid_clips.append(c.without_audio())
                    except: pass

            visual_clips = []
            current_dur = 0.0
            
            # 교차 편집 로직 (사진 3초 -> 영상 4초)
            if vid_clips and imgs:
                while current_dur < SHORTS_DURATION:
                    img = random.choice(imgs)
                    zoom = (lambda t: 1+0.02*t) if random.random() > 0.5 else (lambda t: 1.05-0.02*t)
                    ic = img.with_duration(3.0).resized(width=TARGET_WIDTH).resized(zoom)
                    visual_clips.append(ic)
                    current_dur += 3.0
                    
                    if current_dur >= SHORTS_DURATION: break
                    
                    vc_source = random.choice(vid_clips)
                    max_start = max(0, vc_source.duration - 4.0)
                    start_t = random.uniform(0, max_start)
                    end_t = min(start_t + 4.0, vc_source.duration)
                    vc = vc_source.subclipped(start_t, end_t).resized(width=TARGET_WIDTH)
                    visual_clips.append(vc)
                    current_dur += (end_t - start_t)

            elif vid_clips:
                while current_dur < SHORTS_DURATION:
                    vc_source = random.choice(vid_clips)
                    max_start = max(0, vc_source.duration - 5.0)
                    start_t = random.uniform(0, max_start)
                    end_t = min(start_t + 5.0, vc_source.duration)
                    vc = vc_source.subclipped(start_t, end_t).resized(width=TARGET_WIDTH)
                    visual_clips.append(vc)
                    current_dur += (end_t - start_t)
            elif imgs:
                clip_dur = max(SHORTS_DURATION / len(imgs), 3.0)
                while current_dur < SHORTS_DURATION:
                    for img in imgs:
                        if current_dur >= SHORTS_DURATION: break
                        zoom = (lambda t: 1+0.03*t) if random.random() > 0.5 else (lambda t: 1.05-0.03*t)
                        ic = img.with_duration(clip_dur).resized(width=TARGET_WIDTH).resized(zoom)
                        visual_clips.append(ic)
                        current_dur += clip_dur
            else:
                visual_clips.append(ColorClip(size=(TARGET_WIDTH, TARGET_HEIGHT), color=(0,0,0)).with_duration(SHORTS_DURATION))

            # 클립 이어붙이기
            raw_stream = concatenate_videoclips(visual_clips, method="compose").subclipped(0, SHORTS_DURATION)

            # 앰비언트 배경 덧씌우기
            bg_full = raw_stream.resized(height=TARGET_HEIGHT).cropped(
                width=TARGET_WIDTH, height=TARGET_HEIGHT, x_center=TARGET_WIDTH/2, y_center=TARGET_HEIGHT/2
            )
            dark_overlay = ColorClip(size=(TARGET_WIDTH, TARGET_HEIGHT), color=(0,0,0)).with_duration(SHORTS_DURATION).with_opacity(0.8)
            center_video = raw_stream.with_position('center')
            
            visual_layers = [bg_full, dark_overlay, center_video]

            if self.check_stop(): self.finish_signal.emit("중지됨|0"); return

            # 3. 텍스트 레이어 합성
            self.progress_signal.emit(70)
            
            # 상단 제목 (에러 방지용 \n 포함)
            title_text = TextClip(text=f"{title}\n", font=FONT_PATH, font_size=60, color='yellow', stroke_color='black', stroke_width=2, method='label')
            title_clip = title_text.with_position(('center', 250)).with_duration(SHORTS_DURATION)
            visual_layers.append(title_clip)

            # 하단 고정 어그로 자막 (무료 버전의 핵심 포인트)
            bottom_text = TextClip(text="🔥 화제의 명작!\n지금 바로 확인하세요\n", font=FONT_PATH, font_size=45, color='white', stroke_color='black', stroke_width=2, method='label', text_align='center')
            bottom_clip = bottom_text.with_position(('center', TARGET_HEIGHT - 350)).with_duration(SHORTS_DURATION)
            visual_layers.append(bottom_clip)

            # 4. 오디오 길이 맞추기 및 최종 합성
            final_video = CompositeVideoClip(visual_layers, size=(TARGET_WIDTH, TARGET_HEIGHT))
            
            if master_audio is not None:
                if master_audio.duration < SHORTS_DURATION:
                    loops = int(SHORTS_DURATION / master_audio.duration) + 1
                    master_audio = concatenate_audioclips([master_audio] * loops)
                master_audio = master_audio.subclipped(0, SHORTS_DURATION)
                final_video = final_video.with_audio(master_audio)

            if self.check_stop(): self.finish_signal.emit("중지됨|0"); return

            # 5. 최종 렌더링
            self.progress_signal.emit(80)
            now = datetime.datetime.now()
            save_dir = os.path.abspath(os.path.join(BASE_OUTPUT_FOLDER, now.strftime("%Y-%m-%d")))
            os.makedirs(save_dir, exist_ok=True)
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            final_out_path = os.path.join(save_dir, f"{safe_title}_{now.strftime('%H%M')}.mp4")
            temp_out_path = os.path.join(save_dir, "temp_render.mp4")
            
            self.log(f"🔥 오디오/비주얼 최종 렌더링 중... (CPU 풀가동)")
            final_video.write_videofile(temp_out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=os.path.join(TEMP_FOLDER, "temp_audio.m4a"), remove_temp=True, logger=None)
                
            self.progress_signal.emit(100)
            end_time = time.time()
            elapsed_sec = int(end_time - start_time)
            minutes, seconds = divmod(elapsed_sec, 60)
            time_str = f"{minutes}분 {seconds}초"

            if self.check_stop(): 
                if os.path.exists(temp_out_path): os.remove(temp_out_path)
                self.finish_signal.emit("중지됨|0")
                return

            if os.path.exists(temp_out_path):
                os.rename(temp_out_path, final_out_path)
                self.log(f"✨ 완성! 무료 배포용 숏츠가 생성되었습니다: {final_out_path}")
                self.log(f"⏱️ 작업 소요 시간: {time_str}")
                self.finish_signal.emit(f"성공|{time_str}")
            else:
                self.log("🔥 렌더링 실패")
                self.finish_signal.emit("실패|0")

        except Exception as e:
            self.log(f"❌ 에러 발생: {e}")
            self.finish_signal.emit("실패|0")
        finally:
            if os.path.exists(TEMP_FOLDER): shutil.rmtree(TEMP_FOLDER, ignore_errors=True); time.sleep(0.5)
            gc.collect()

# ==============================================================================
# [GUI 화면]
# ==============================================================================
class ShortsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("AI_Shorts_Maker_Free", "Settings")
        self.current_movie_info = None 
        self.is_making_video = False 
        
        self.initUI()
        self.load_geometry() 

    def load_geometry(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def initUI(self):
        self.setWindowTitle('🎬 영화 리뷰 숏츠 메이커 (무료 배포용)')
        self.setGeometry(200, 200, 550, 700)
        self.setCursor(Qt.ArrowCursor) 
        layout = QVBoxLayout()

        gb_mode = QGroupBox("1단계: 영화 선택하기")
        v_mode = QVBoxLayout()
        
        self.radio_manual = QRadioButton("✏️ 직접 입력하기")
        self.radio_manual.setChecked(True)
        self.radio_manual.toggled.connect(self.toggle_input)
        self.radio_manual.setCursor(Qt.PointingHandCursor)
        v_mode.addWidget(self.radio_manual)

        h_manual = QHBoxLayout()
        self.input_title = KoreanLineEdit()
        self.input_title.setPlaceholderText("제목 입력 후 엔터키를 치세요")
        self.input_title.setStyleSheet("font-size: 14px; padding: 5px;")
        self.input_title.setCursor(Qt.IBeamCursor)
        self.input_title.returnPressed.connect(self.search_movie) 
        h_manual.addWidget(self.input_title)
        v_mode.addLayout(h_manual)

        v_mode.addSpacing(10)

        self.radio_random = QRadioButton("🎲 장르 무작위 뽑기")
        self.radio_random.toggled.connect(self.toggle_input)
        self.radio_random.setCursor(Qt.PointingHandCursor)
        v_mode.addWidget(self.radio_random)

        grid_genre = QGridLayout()
        self.bg_genre = QButtonGroup()
        
        row, col = 0, 0
        for idx, genre in enumerate(GENRE_MAP.keys()):
            rb = QRadioButton(genre)
            if idx == 0: rb.setChecked(True)
            rb.setEnabled(False)
            rb.setCursor(Qt.PointingHandCursor)
            self.bg_genre.addButton(rb)
            grid_genre.addWidget(rb, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
        v_mode.addLayout(grid_genre)
        gb_mode.setLayout(v_mode)
        layout.addWidget(gb_mode)

        h_buttons = QHBoxLayout()
        
        self.btn_search = QPushButton("🔍 1. 영화 검색하기")
        self.btn_search.setMinimumHeight(45)
        self.btn_search.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white; font-size: 14px;")
        self.btn_search.setCursor(Qt.PointingHandCursor)
        self.btn_search.clicked.connect(self.search_movie)
        h_buttons.addWidget(self.btn_search)

        self.btn_action = QPushButton("🚀 2. 숏츠 만들기 (무료)")
        self.btn_action.setMinimumHeight(45)
        self.btn_action.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; font-size: 14px;")
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.setEnabled(False) 
        self.btn_action.clicked.connect(self.handle_action_btn)
        h_buttons.addWidget(self.btn_action)

        layout.addLayout(h_buttons)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-size: 13px;")
        layout.addWidget(self.log_area)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.pbar.setAlignment(Qt.AlignCenter)
        self.pbar.setStyleSheet("""
            QProgressBar { border: 2px solid grey; border-radius: 5px; text-align: center; background-color: #333; color: white; font-weight: bold; } 
            QProgressBar::chunk {background-color: #05B8CC;}
        """)
        layout.addWidget(self.pbar)

        self.setLayout(layout)

    def toggle_input(self):
        is_manual = self.radio_manual.isChecked()
        self.input_title.setEnabled(is_manual)
        for btn in self.bg_genre.buttons():
            btn.setEnabled(not is_manual)

    def log(self, text):
        self.log_area.append(text)
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum()) 

    def update_progress(self, val):
        self.pbar.setValue(val)

    def search_movie(self):
        self.log_area.clear()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.current_movie_info = None
        self.btn_action.setEnabled(False) 
        
        mode = 'MANUAL' if self.radio_manual.isChecked() else 'RANDOM'
        
        if mode == 'MANUAL':
            title = self.input_title.text().strip()
            if not title:
                QMessageBox.warning(self, "경고", "영화 제목을 먼저 입력해주세요!")
                return
            self.log(f"🔎 '{title}' 영화 정보를 찾는 중...")
            QApplication.processEvents() 
            movie_info = get_manual_movie(title)
        else:
            genre = self.bg_genre.checkedButton().text()
            genre_id = GENRE_MAP[genre]
            self.log(f"🎲 '{genre}' 장르에서 랜덤으로 영화를 고르는 중...")
            QApplication.processEvents()
            movie_info = get_random_movie(genre_id)

        if not movie_info:
            QMessageBox.warning(self, "실패", "영화 정보를 찾을 수 없습니다. 다른 검색어나 장르를 선택해주세요.")
            self.log("❌ 탐색 실패.")
            return

        self.current_movie_info = movie_info
        self.log("=========================================")
        self.log(f"✅ 선택된 영화: [{movie_info['title']}]")
        self.log(f"👉 이제 [🚀 2. 숏츠 만들기] 버튼을 눌러 작업을 시작하세요!")
        
        self.btn_action.setEnabled(True) 
        self.btn_action.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; font-size: 14px;")

    def handle_action_btn(self):
        if not self.is_making_video:
            self.start_video()
        else:
            self.stop_video()

    def start_video(self):
        if not self.current_movie_info:
            QMessageBox.warning(self, "오류", "먼저 영화를 검색해주세요!")
            return

        self.is_making_video = True
        self.btn_search.setEnabled(False) 
        self.btn_action.setText("⏹️ 제작 정지하기")
        self.btn_action.setStyleSheet("font-weight: bold; background-color: #F44336; color: white; font-size: 14px;")
        
        self.log("=========================================")
        self.log(f"🚀 [{self.current_movie_info['title']}] 숏츠 제작 시작!")
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)

        self.worker = VideoMakerThread(self.current_movie_info)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finish_signal.connect(self.process_finished)
        self.worker.start()

    def stop_video(self):
        self.log("=========================================")
        self.log("🛑 [정지 요청됨] 진행 중인 작업을 안전하게 정리하고 있습니다...")
        self.log("⚠️ (렌더링 중일 경우, 완전히 멈출 때까지 수 초가 소요될 수 있습니다.)")
        self.worker.stop() 
        self.pbar.setRange(0, 0) 
        self.btn_action.setText("⏳ 정지하는 중...")
        self.btn_action.setStyleSheet("font-weight: bold; background-color: #757575; color: white; font-size: 14px;")
        self.btn_action.setEnabled(False)

    def process_finished(self, result_data):
        self.is_making_video = False
        self.btn_search.setEnabled(True)
        self.btn_action.setEnabled(True)
        self.btn_action.setText("🚀 2. 숏츠 만들기 (무료)")
        self.btn_action.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; font-size: 14px;")
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.log("=========================================")
        
        result, time_str = result_data.split("|")
        
        if result == "성공":
            QMessageBox.information(self, "작업 완료", f"🎉 무료 숏츠 영상이 성공적으로 생성되었습니다!\n\n⏱️ 소요 시간: {time_str}\n📁 outputs 폴더를 확인하세요.")
        elif result == "중지됨":
            self.log("✅ 작업이 완전히 정지되었으며, 임시 파일들이 삭제되었습니다.")
            QMessageBox.warning(self, "정지 완료", "안전하게 작업이 정지되었습니다.")
        else:
            QMessageBox.warning(self, "실패", "영상 생성 중 문제가 발생했습니다. 로그를 확인하세요.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ShortsApp()
    ex.show()
    sys.exit(app.exec_())