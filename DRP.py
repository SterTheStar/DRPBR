# DRP - A repository program for downloading operating systems.
# Copyright (C) 2024 Esther
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# Project Name: DRP
# Original Author: Esther
# License: GNU General Public License v3.0
#
# This code was originally created by Esther.
# If you modify this code, please keep this notice and mention the original author.

# DRP Copyright (C) 2024 Esther
# This program comes with ABSOLUTELY NO WARRANTY;
# This is free software, and you are welcome to redistribute it under certain conditions;

# For more information, contact: @onlysterbr Twitter (X)

import sys
import json
import urllib.request
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QComboBox, QMessageBox, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar, QLineEdit, QTextEdit, QDialog, QScrollArea
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSettings
from PyQt5.QtGui import QDesktopServices
from qtmodern.styles import dark
from qtmodern.windows import ModernWindow
from packaging.version import Version

class DownloadThread(QThread):
    update_progress = pyqtSignal(int)
    update_speed = pyqtSignal(float, QProgressBar)

    def __init__(self, url, save_path, progress_bar, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = save_path
        self.progress_bar = progress_bar
        self.start_time = None
        self.downloaded_bytes = 0
        self._terminate = False

    def run(self):
        try:
            self.start_time = time.time()
            self.request, _ = urllib.request.urlretrieve(self.url, self.save_path, reporthook=self.report_hook)
        except Exception as e:
            print(f"Download error: {e}")

    def report_hook(self, blocknum, blocksize, totalsize):
        if self._terminate:
            raise Exception("Download cancelled by user.")
        if totalsize > 0:
            self.downloaded_bytes += blocksize
            progress = blocknum * blocksize * 100 / totalsize
            self.update_progress.emit(int(progress))
            
            elapsed_time = time.time() - self.start_time
            download_speed = (self.downloaded_bytes / 1024 / 1024) / elapsed_time if elapsed_time > 0 else 0
            self.update_speed.emit(download_speed, self.progress_bar)

    def terminate(self):
        self._terminate = True
        urllib.request.urlcleanup()

class LicenseDialog(QDialog):
    def __init__(self, license_text, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('License')

        layout = QVBoxLayout(self)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(license_text)

        scroll_area.setWidget(text_edit)

        layout.addWidget(scroll_area)

        self.setMinimumWidth(600)  # Definindo a largura mínima da janela

        self.setLayout(layout)
            
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings_file = 'config.json'  # Nome do arquivo de configuração JSON
        self.settings = QSettings("MyCompany", "MyApp")

        self.load_settings()

        self.setWindowTitle('Download ISO do Windows')
        self.setGeometry(200, 200, 600, 400)

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.official_os_tab = self.create_os_tab('https://raw.githubusercontent.com/SterTheStar/DRPBR/main/repositorio.json', 'Official OS')
        self.mod_os_tab = self.create_os_tab('https://raw.githubusercontent.com/SterTheStar/DRPBR/main/modosrepositorio.json', 'Mod OS')
        self.settings_tab = self.create_settings_tab()

        self.tab_widget.addTab(self.official_os_tab, 'Official OS')
        self.tab_widget.addTab(self.mod_os_tab, 'Mod OS')
        self.tab_widget.addTab(self.settings_tab, 'Settings')

        QTimer.singleShot(100, self.check_and_display_changelog)

        self.download_thread = None

    def load_settings(self):
        self.settings.beginGroup("DownloadSettings")
        self.download_path = self.settings.value("download_path", "")
        self.download_speed = self.settings.value("download_speed", 0)
        self.settings.endGroup()

    def save_settings(self):
        self.settings.beginGroup("DownloadSettings")
        self.settings.setValue("download_path", self.download_path)
        self.settings.setValue("download_speed", self.download_speed)
        self.settings.endGroup()

    def create_os_tab(self, json_url, tab_name):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title_label = QLabel(f'DRP {tab_name}', tab)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 14))
        layout.addWidget(title_label)

        combo_layout1 = QHBoxLayout()
        layout.addLayout(combo_layout1)

        select_os_label = QLabel('Select OS:', tab)
        select_os_label.setAlignment(Qt.AlignLeft)
        combo_layout1.addWidget(select_os_label)

        combo_windows = QComboBox(tab)
        combo_layout1.addWidget(combo_windows)

        combo_layout2 = QHBoxLayout()
        layout.addLayout(combo_layout2)

        select_arch_label = QLabel('Select Architecture:', tab)
        select_arch_label.setAlignment(Qt.AlignLeft)
        combo_layout2.addWidget(select_arch_label)

        combo_arch = QComboBox(tab)
        combo_layout2.addWidget(combo_arch)

        combo_layout3 = QHBoxLayout()
        layout.addLayout(combo_layout3)

        select_version_label = QLabel('Select Version:', tab)
        select_version_label.setAlignment(Qt.AlignLeft)
        combo_layout3.addWidget(select_version_label)

        combo_version = QComboBox(tab)
        combo_layout3.addWidget(combo_version)

        # Layout horizontal para os botões
        button_layout = QHBoxLayout()

        btn_download = QPushButton('Download', tab)
        button_layout.addWidget(btn_download)

        btn_cancel = QPushButton('Cancel', tab)
        btn_cancel.setEnabled(False)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)  # Adiciona o layout dos botões ao layout principal

        progress_bar = QProgressBar(tab)
        layout.addWidget(progress_bar)

        try:
            download_data = self.load_data_from_json(json_url)
            combo_windows.addItems([entry['windows_version'] for entry in download_data])
            
            # Configuração inicial dos combos
            if download_data:
                self.on_windows_version_changed(combo_windows, combo_arch, combo_version, download_data)
                combo_windows.setCurrentIndex(0)  # Define o primeiro item como selecionado inicialmente

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load JSON data: {e}')

        combo_windows.currentIndexChanged.connect(lambda: self.on_windows_version_changed(combo_windows, combo_arch, combo_version, download_data))
        combo_arch.currentIndexChanged.connect(lambda: self.on_architecture_changed(combo_windows, combo_arch, combo_version, download_data))
        btn_download.clicked.connect(lambda: self.download_iso(combo_windows, combo_arch, combo_version, download_data, progress_bar, btn_cancel))
        btn_cancel.clicked.connect(self.cancel_download)

        # Novo layout para a configuração de download

        button_layout2 = QHBoxLayout()
        btn_open_browser = QPushButton('Download in WebBrowser', tab)
        button_layout2.addWidget(btn_open_browser)
        layout.addLayout(button_layout2)

        btn_open_browser.clicked.connect(lambda: self.open_in_browser(combo_windows, combo_arch, combo_version, download_data))

        return tab

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        settings_layout = QHBoxLayout()

        download_path_label = QLabel('Download Path:', tab)
        settings_layout.addWidget(download_path_label)

        self.download_path_edit = QLineEdit()
        settings_layout.addWidget(self.download_path_edit)

        btn_choose_path = QPushButton('🔎', tab)
        settings_layout.addWidget(btn_choose_path)

        layout.addLayout(settings_layout)

        # Adicionando espaçamento flexível para empurrar os botões para a parte inferior
        layout.addStretch()

        # Nova linha para os botões na parte inferior alinhados à esquerda
        bottom_layout = QHBoxLayout()

        btn_source_code = QPushButton('Source Code', tab)
        btn_source_code.setMinimumWidth(100)  # Definindo largura mínima
        bottom_layout.addWidget(btn_source_code)

        btn_creator = QPushButton('Creator', tab)
        btn_creator.setMinimumWidth(100)  # Definindo largura mínima
        bottom_layout.addWidget(btn_creator)

        btn_license = QPushButton('License', tab)
        btn_license.setMinimumWidth(100)  # Definindo largura mínima
        bottom_layout.addWidget(btn_license)


        layout.addLayout(bottom_layout)

        # Adicionando o botão "Save Settings" em uma linha separada abaixo dos botões acima
        layout.addSpacing(0)  # Espaçamento entre as linhas
        btn_save_settings = QPushButton('Save Settings', tab)
        btn_save_settings.setMinimumWidth(580)  # Definindo largura mínima
        layout.addWidget(btn_save_settings, alignment=Qt.AlignLeft)  # Alinhando à esquerda

        # Conectando os sinais aos slots (eventos)
        btn_source_code.clicked.connect(self.open_source_code)
        btn_creator.clicked.connect(self.open_creator)
        btn_choose_path.clicked.connect(self.choose_download_path)
        btn_save_settings.clicked.connect(self.save_settings)
        btn_license.clicked.connect(self.show_license)

        return tab
    
    def show_license(self):
        try:
            with open('license.json', 'r', encoding='utf-8') as f:
                license_text = f.read()

                license_dialog = LicenseDialog(license_text, self)
                license_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load license: {e}')
    
    def open_source_code(self):
        QDesktopServices.openUrl(QUrl('https://github.com/SterTheStar/DRPBR/'))

    def open_creator(self):
        QDesktopServices.openUrl(QUrl('https://github.com/SterTheStar'))

    def choose_download_path(self):
        download_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if download_path:
            self.download_path = download_path
            self.download_path_edit.setText(download_path)
            self.save_settings()

    def on_windows_version_changed(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        combo_arch.clear()
        combo_version.clear()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            combo_arch.addItems([version['architecture'] for version in versions])

            if versions:
                self.on_architecture_changed(combo_windows, combo_arch, combo_version, download_data)

    def on_architecture_changed(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        combo_version.clear()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    combo_version.addItems(version['versions'].keys())

    def download_iso(self, combo_windows, combo_arch, combo_version, download_data, progress_bar, btn_cancel):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        selected_version = combo_version.currentText()

        btn_download = self.sender()
        btn_download.setEnabled(False)
        btn_cancel.setEnabled(True)

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    if selected_version in version['versions']:
                        download_url = version['versions'][selected_version]
                        save_path = f"{self.download_path}/{selected_version}.iso"
                        speed_limit = self.download_speed
                        self.download_thread = DownloadThread(download_url, save_path, progress_bar)
                        self.download_thread.update_progress.connect(progress_bar.setValue)
                        self.download_thread.update_speed.connect(self.update_download_speed)
                        self.download_thread.start()
                        self.download_thread.finished.connect(lambda: self.on_download_finished(btn_cancel, btn_download))
                        return

        QMessageBox.warning(self, 'Link not found', f'Failed to find a download link for {selected_architecture} {selected_version}.')

    def update_download_speed(self, speed, progress_bar):
        current_progress = progress_bar.value()
        if current_progress < 100:
            progress_bar.setFormat(f"Downloading... {current_progress}% - Speed: {speed:.2f} MB/s")
        else:
            progress_bar.setFormat(f"Completed.")

    def on_download_finished(self, btn_cancel, btn_download):
        btn_cancel.setEnabled(False)
        btn_download.setEnabled(True)

        QMessageBox.information(self, 'Download Completed', 'Completed.')

    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()

    def open_in_browser(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        selected_version = combo_version.currentText()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    if selected_version in version['versions']:
                        download_url = version['versions'][selected_version]
                        QDesktopServices.openUrl(QUrl(download_url))

    def open_in_browser(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        selected_version = combo_version.currentText()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    if selected_version in version['versions']:
                        download_url = version['versions'][selected_version]
                        QDesktopServices.openUrl(QUrl(download_url))

    def check_and_display_changelog(self):
        url = 'https://raw.githubusercontent.com/SterTheStar/DRPBR/main/changelogs.json'

        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode()
                changelogs = json.loads(content)

                latest_version = max(changelogs.keys(), key=lambda v: Version(v))
                changelog_info = changelogs[latest_version]

                if changelog_info.get('show_changelog', False):
                    changelog_text = f"Version: {changelog_info['version']}\n"
                    changelog_text += f"Date: {changelog_info['date']}\n\n"
                    changelog_text += "Changes:\n"
                    for change in changelog_info['changes']:
                        changelog_text += f"- {change}\n"

                    QMessageBox.information(self, 'Changelog', changelog_text)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load changelog: {e}')

    def load_data_from_json(self, url):
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode()
                return json.loads(data)
        except Exception as e:
            raise Exception(f"Failed to load JSON data from {url}: {e}")

def main():
    app = QApplication(sys.argv)
    dark(app)
    window = ModernWindow(MainWindow())
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()