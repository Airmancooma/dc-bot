from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
import vlc
import sys
import datetime
import whisper
from typing import Iterator, TextIO
import os
import srt

class TranscribeThread(QtCore.QThread):
    signal = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, file, model):
        super().__init__()
        self.file = file
        self.model = model

    def run(self):
        result = self.model.transcribe(self.file)
        self.signal.emit(result)


class Player(QtWidgets.QMainWindow):
    MIN_WINDOW_HEIGHT = 480
    MAX_WINDOW_HEIGHT = 1080
    MIN_FONT_SIZE = 12
    MAX_FONT_SIZE = 26
    MIN_SUBTITLE_HEIGHT = 20
    MAX_SUBTITLE_HEIGHT = 70
    MIN_SLIDER_HEIGHT = 20
    MAX_SLIDER_HEIGHT = 50

    def __init__(self, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.setWindowTitle("Media Player")

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        self.file = None
        self.create_ui()
        self.is_paused = False
        self.user_moving_slider = False

        self.whisper_model = whisper.load_model("base")

    def create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        self.video_frame = QtWidgets.QFrame()
        self.palette = self.video_frame.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.video_frame.setPalette(self.palette)
        self.video_frame.setAutoFillBackground(True)

        self.open_button = QtWidgets.QPushButton("Open")
        self.open_button.clicked.connect(self.open_file)

        self.play_button = QtWidgets.QPushButton("Play")
        self.play_button.clicked.connect(self.play_pause)

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)

        self.fullscreen_button = QtWidgets.QPushButton("Fullscreen")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setFixedHeight(self.MIN_SLIDER_HEIGHT)
        self.slider.sliderMoved.connect(self.set_position)

        self.slider_layout = QtWidgets.QHBoxLayout()
        self.label_current_time = QtWidgets.QLabel()
        self.label_duration = QtWidgets.QLabel()
        self.slider_layout.addWidget(self.label_current_time)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.label_duration)

        self.slider_widget = QtWidgets.QWidget()
        self.slider_widget.setLayout(self.slider_layout)
        self.slider_widget.setFixedHeight(50)

        self.h_box = QtWidgets.QHBoxLayout()
        self.h_box.addWidget(self.open_button)
        self.h_box.addWidget(self.play_button)
        self.h_box.addWidget(self.stop_button)
        self.h_box.addWidget(self.fullscreen_button)

        self.buttons_widget = QtWidgets.QWidget()
        self.buttons_widget.setLayout(self.h_box)
        self.buttons_widget.setFixedHeight(50)

        self.subtitle_label = QtWidgets.QLabel()
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(QtCore.Qt.AlignCenter)  # center align text
        self.subtitle_label.setStyleSheet("margin: 0; padding: 0")  # set margin and padding to 0
        self.subtitle_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        font = self.subtitle_label.font()
        font.setPointSize(self.MIN_FONT_SIZE)
        self.subtitle_label.setFont(font)
        self.subtitle_label.setFixedHeight(self.MIN_SUBTITLE_HEIGHT)

        self.v_box = QtWidgets.QVBoxLayout()
        self.v_box.addWidget(self.video_frame)
        self.v_box.addWidget(self.subtitle_label)  # move subtitle label here
        self.v_box.addWidget(self.slider_widget)
        self.v_box.addWidget(self.buttons_widget)
        self.v_box.setContentsMargins(0, 0, 0, 0)

        self.widget.setLayout(self.v_box)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_ui)

    def resizeEvent(self, event):
        height_ratio = (self.height() - self.MIN_WINDOW_HEIGHT) / (self.MAX_WINDOW_HEIGHT - self.MIN_WINDOW_HEIGHT)
        font_size = self.MIN_FONT_SIZE + height_ratio * (self.MAX_FONT_SIZE - self.MIN_FONT_SIZE)
        subtitle_height = self.MIN_SUBTITLE_HEIGHT + height_ratio * (self.MAX_SUBTITLE_HEIGHT - self.MIN_SUBTITLE_HEIGHT)
        slider_height = self.MIN_SLIDER_HEIGHT + height_ratio * (self.MAX_SLIDER_HEIGHT - self.MIN_SLIDER_HEIGHT)

        font = self.subtitle_label.font()
        font.setPointSize(max(min(int(font_size), self.MAX_FONT_SIZE), self.MIN_FONT_SIZE))
        self.subtitle_label.setFont(font)
        self.subtitle_label.setFixedHeight(max(min(int(subtitle_height), self.MAX_SUBTITLE_HEIGHT), self.MIN_SUBTITLE_HEIGHT))
        self.slider.setFixedHeight(max(min(int(slider_height), self.MAX_SLIDER_HEIGHT), self.MIN_SLIDER_HEIGHT))

        super().resizeEvent(event)

    def open_file(self):
        self.file = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "/home", "Videos (*.mp4 *.avi *.mkv *.flv *.mov)")[0]
        if self.file:
            self.media = self.instance.media_new(self.file)
            self.media_player.set_media(self.media)
            self.media.parse()
            self.setWindowTitle(self.media.get_meta(0))
            self.media_player.set_xwindow(int(self.video_frame.winId()))

            # Create 'subtitles' folder in the same directory as the video file
            self.srt_dir = os.path.join(os.path.dirname(self.file), 'subtitles-for-videos')
            os.makedirs(self.srt_dir, exist_ok=True)

            self.srt_path = os.path.join(self.srt_dir, os.path.basename(self.file).rsplit(".", 1)[0] + "_subs.srt")
            if not os.path.exists(self.srt_path):
                self.transcribe_thread = TranscribeThread(self.file, self.whisper_model)
                self.transcribe_thread.signal.connect(self.on_transcription_ready)
                self.transcribe_thread.start()

                self.progress = QProgressDialog("Generating...", None, 0, 0, self)
                self.progress.setWindowTitle("Please Wait")
                self.progress.setModal(True)
                self.progress.setCancelButton(None)
                self.progress.rejected.connect(self.on_progress_rejected)
                self.progress.show()

                self.play_button.setEnabled(False)
            else:
                self.load_subs()
                self.play_button.setEnabled(True)
                self.play_pause()

    def on_progress_rejected(self):
        reply = QMessageBox.question(self, 'Confirmation', "Are you sure you want to cancel the generation?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.transcribe_thread.stop()

    def on_transcription_ready(self, result):
        self.play_button.setEnabled(True)
        self.play_pause()
        self.progress.close()
        self.create_subtitle_file(result)
        self.load_subs()

    def play_pause(self):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_button.setText('Play')
            self.is_paused = True
            self.timer.stop()
        else:
            if self.media_player.play() == -1:
                self.open_file()
                return
            self.media_player.play()
            self.play_button.setText('Pause')
            self.timer.start()
            self.is_paused = False

    def stop(self):
        self.media_player.stop()
        self.play_button.setText('Play')

    def toggle_fullscreen(self):
        if self.windowState() & QtCore.Qt.WindowFullScreen:
            self.showNormal()
            self.buttons_widget.show()  # Vezérlők megjelenítése
            self.slider_widget.show()   # Csúszka megjelenítése
        else:
            self.showFullScreen()
            self.buttons_widget.hide()  # Vezérlők elrejtése
        self.slider_widget.hide()   # Csúszka elrejtése


    def update_ui(self):
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        if not self.user_moving_slider:
            self.slider.setSliderPosition(int(self.position() * 1000))

        self.label_current_time.setText(str(datetime.timedelta(seconds=int(self.media_player.get_time() / 1000))))
        self.label_duration.setText(str(datetime.timedelta(seconds=int(self.media.get_duration() / 1000))))
        self.update_subs()

    def position(self):
        return self.media_player.get_position()

    def set_position(self, position):
        self.user_moving_slider = True
        self.media_player.set_position(position / 1000.0)
        self.user_moving_slider = False

    def load_subs(self):
        with open(self.srt_path, 'r') as f:
            self.subs = list(srt.parse(f))
        self.current_sub_idx = -1

    def update_subs(self):
        if not self.subs:
            return
        current_time = self.media_player.get_time() / 1000.0
        for i, sub in enumerate(self.subs):
            if sub.start.total_seconds() <= current_time < sub.end.total_seconds():
                self.current_sub_idx = i
                self.subtitle_label.setText(sub.content)
                return
        self.subtitle_label.setText("")

    def create_subtitle_file(self, result):
        # Write the transcription result into the .srt file
        with open(self.srt_path, "w", encoding="utf-8") as srt:
            self.write_srt(result["segments"], file=srt)

    @staticmethod
    def write_srt(transcript: Iterator[dict], file: TextIO):
        for i, segment in enumerate(transcript, start=1):
            print(
                f"{i}\n"
                f"{Player.format_timestamp(segment['start'], always_include_hours=True)} --> "
                f"{Player.format_timestamp(segment['end'], always_include_hours=True)}\n"
                f"{segment['text'].strip().replace('-->', '->')}\n",
                file=file,
                flush=True,
            )

    @staticmethod
    def format_timestamp(seconds: float, always_include_hours: bool = False):
        assert seconds >= 0, "non-negative timestamp expected"
        milliseconds = round(seconds * 1000.0)

        hours = milliseconds // 3_600_000
        milliseconds -= hours * 3_600_000

        minutes = milliseconds // 60_000
        milliseconds -= minutes * 60_000

        seconds = milliseconds // 1_000
        milliseconds -= seconds * 1_000

        hours_marker = f"{hours}:" if always_include_hours or hours > 0 else ""
        return f"{hours_marker}{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    player = Player()
    player.show()
    player.resize(640, 480)
    sys.exit(app.exec_())