from PyQt5.QtWidgets import QMainWindow ,QMessageBox, QApplication,QPushButton,QListWidget, QDoubleSpinBox ,QSpinBox, QWidget, QLabel ,  QSlider, QRadioButton, QComboBox, QTableWidget, QTableWidgetItem, QCheckBox,QMenu,QTextEdit, QDialog, QFileDialog, QInputDialog, QSizePolicy,QScrollArea,QVBoxLayout,QHBoxLayout
from PyQt5.uic import loadUi
import sys
import pyqtgraph as pg
from pyqtgraph import PlotWidget
import os
from Spectrogram import Spectrogram
from Graph import Graph
from PyQt5.QtGui import QIcon
from Load import Load
from Signal import Signal
from sampling import Sampling
import numpy as np
from UniformMode import UniformMode
from MusicMode import MusicMode
from WeinerFilterr import WeinerFilterr
from AnimalAndMusic_Mode import AnimalAndMusic
import sounddevice as sd 
import simpleaudio as sa
from scipy.io import wavfile




class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        loadUi("SignalEqualizerr.ui", self)
        self.setWindowTitle("Signal Equalizer")
        self.setWindowIcon(QIcon("icons/radio-waves.png"))


        
        #hajar
        # Initialize the scale combo box
        self.scale_combo_box = self.findChild(QComboBox, 'scale')
        self.scale_combo_box.setCurrentIndex(0)  # Set default to "Linear Scale"
        self.scale_combo_box.currentIndexChanged.connect(self.change_scale)
        self.sampling = Sampling()
        self.signal=None 
        self.file_path=None
        self.mode_chosen= self.findChild(QComboBox, "mode")
        self.mode_chosen.setCurrentIndex(0)
        self.mode_chosen.currentIndexChanged.connect(self.change_mode)
        self.mode_instance=None
        self.sliders_widget= self.findChild(QWidget, 'slidersWidget') 
        
        self.spectrogram_input = Spectrogram()
        self.spectrogram_output = Spectrogram()


        self.audiobefore = self.findChild(QPushButton, 'audioBefore')
        self.audioafter = self.findChild(QPushButton, 'audioAfter')
        self.signal=None
        self.zoom_in_button = self.findChild(QPushButton, 'zoomIn') 
        self.zoom_in_button.clicked.connect(self.zoom_in) 
        self.zoom_out_button = self.findChild(QPushButton, 'zoomOut') 
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.browsefile = self.findChild(QPushButton, 'browseFile')
        self.browsefile.clicked.connect(self.load_signal)
        self.play = self.findChild(QPushButton, 'play')
        self.play.clicked.connect(self.toggle_play_pause)
        self.removefile = self.findChild(QPushButton, 'removeFile')
        self.removefile.clicked.connect(self.clear_signals)
        self.rewind = self.findChild(QPushButton, "radioButton")
        self.rewind.clicked.connect(self.rewind_signal)
        self.spectrogram_widget1 = self.findChild(QWidget, 'spectogram1') 
        self.spectrogram_widget2 = self.findChild(QWidget, 'spectogram2') 
        self.spectrogram_check = self.findChild(QCheckBox, 'spectogramCheck')
        self.spectrogram_check.stateChanged.connect(self.handle_checkbox_state)
        self.speed = self.findChild(QSlider, 'speedSlider')
        self.speed.setMinimum(0)  # Set minimum zoom value
        self.speed.setMaximum(50)  # Set maximum zoom value
        self.speed.setValue(25)  # Set initial zoom value
        self.speed.valueChanged.connect(self.set_speed_value) 

        self.graph1 = self.findChild(pg.PlotWidget, 'graph1')
        self.graph2 = self.findChild(pg.PlotWidget, 'graph2')
        self.graph3 = self.findChild(pg.PlotWidget, 'graph3')

        self.graph1 = Graph(self.graph1, "Graph 1", "", "")
        self.graph2 = Graph(self.graph2, "Graph 2", "", "")
        self.graph3 = Graph(self.graph3,  "Frequency Domain", "Frequency (Hz)", "Magnitude")
        


        self.load_instance = Load()  # Instance of the Load class

        self.play_icon = QIcon("icons/play.png")
        self.pause_icon = QIcon("icons/pause (2).png")
        self.play.setIcon(self.pause_icon)

        self.audiobefore.setIcon(self.play_icon)
        self.audioafter.setIcon(self.play_icon)
        self.current_icon = 1
        self.audiobefore.setText('Play')
        self.audioafter.setText('Play')

        self.audiobefore.clicked.connect(self.play_original_audio)
        self.audioafter.clicked.connect(self.play_modified_audio)

        # Initialize playback state for both buttons
        self.is_playing_before = False  # For the original audio button
        self.is_playing_after = False   # For the modified audio button

        self.link_graphs()
        #self.change_mode(0)

    def link_graphs(self):
        viewbox1 = self.graph1.graphWidget.getViewBox()
        viewbox2 = self.graph2.graphWidget.getViewBox()
    
        viewbox2.setXLink(viewbox1)  
        viewbox2.setYLink(viewbox1)  

        viewbox1.setLimits(xMin=0)
        viewbox2.setLimits(xMin=0)        

    def set_speed_value(self, value):
        # Map the slider value to a sensible range for QTimer interval
        # Slider value (0 to 50) -> Timer interval (200ms to 10ms)
        min_interval = 5  # Minimum interval (fastest updates)
        max_interval = 200  # Maximum interval (slowest updates)
        
        # Invert the slider mapping
        interval = max_interval - (max_interval - min_interval) * (value / self.speed.maximum())
        
        # Set the timer interval
        self.graph1.set_speed(interval)
        self.graph2.set_speed(interval)


    def zoom_in(self):
        self.graph1.zoom_in() 
        self.graph2.zoom_in()

    def zoom_out(self):
        self.graph1.zoom_out() 
        self.graph2.zoom_out() 

   


    def handle_checkbox_state(self): 
        if self.spectrogram_check.isChecked(): 
            self.spectrogram_widget1.setVisible(False) 
            self.spectrogram_widget2.setVisible(False) 
            print("PlotWidgets are hidden") 
        else: 
            self.spectrogram_widget1.setVisible(True) 
            self.spectrogram_widget2.setVisible(True) 
            print("PlotWidgets are visible")


    def change_scale(self,selected_scale):
        """Update the graph to use either linear or audiogram scale based on combo box selection."""
        selected_scale = self.scale_combo_box.currentText()
       
        if selected_scale == "Audiogram Scale":
            self.sampling.set_scale(True)  # Set to audiogram (logarithmic) scale
            self.mode_instance.set_is_audiogram(True)
            is_audiogram= True
        else:
            self.sampling.set_scale(False)  # Set to linear scale
            is_audiogram= False

        # Re-plot frequency domain with the selected scale
        if self.signal.signal_data_time is not None and self.signal.signal_data_amplitude is not None:
            self.sampling.plot_frequency_domain(self.sampling.get_frequencies(),self.sampling.get_magnitudes(), is_audiogram, self.graph3)        



    
    def _prepare_data(self, data):
        """ Normalize and prepare data for playback """
        # Normalize the audio data
        data = data.astype(np.float32)
        data /= np.max(np.abs(data)) if np.max(np.abs(data)) != 0 else 1.0

        # Convert stereo to mono if needed
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # Convert to mono

        return data

    def play_audio(self, data):
        """ Play audio using sounddevice and wait until it's done """
        try:
            # Prepare the data
            data = self._prepare_data(data)
            
            # Play audio and wait for it to finish
            sd.play(data, samplerate=self.signal.sample_rate)
            # sd.wait()  

            print("Audio playback completed.")
        except Exception as e:
            print(f"Error while playing sound: {e}")

    def play_original_audio(self):
        """Toggle play/pause for the original audio."""
        if not self.is_playing_before:  # If not playing, start playing
            if self.signal is not None:
                data = self.signal.signal_data_amplitude
                self.play_audio(data)

                # Update button state and icon to 'pause'
                self.audiobefore.setIcon(self.pause_icon)  # Replace with pause icon
                self.audiobefore.setText('Pause')
                self.is_playing_before = True
        else:  # If playing, pause it
            sd.stop()  # Stop audio playback
            self.audiobefore.setIcon(self.play_icon)  # Replace with play icon
            self.audiobefore.setText('Play')
            self.is_playing_before = False  

    def play_modified_audio(self):
        """Toggle play/pause for the modified audio."""
        if not self.is_playing_after:  # If not playing, start playing
            if self.mode_instance is not None:
                if self.mode_instance.get_inverse() is not None:
                    data = self.mode_instance.get_inverse()
                else:
                    data = self.signal.signal_data_amplitude

                if data is not None:
                    self.play_audio(data)

                    # Update button state and icon to 'pause'
                    self.audioafter.setIcon(self.pause_icon)  # Replace with pause icon
                    self.audioafter.setText('Pause')
                    self.is_playing_after = True
        else:  # If playing, pause it
            sd.stop()  # Stop audio playback
            self.audioafter.setIcon(self.play_icon)  # Replace with play icon
            self.audioafter.setText('Play')
            self.is_playing_after = False

            
        

    def load_signal(self): 
            self.file_path = self.load_instance.browse_signals() 
            self.clear_signals()
            
            if self.file_path: 
                # Handle the loaded signal 
                # For example, load the signal data into a graph 
                try: 
                    self.prepare_load(self.file_path)
                except Exception as e: 
                    QMessageBox.warning(self, "Error", f"Failed to load signal: {e}") 
            self.mode_instance.reset_sliders_to_default()  
            current_scale=self.scale_combo_box.currentText()
            self.change_scale(current_scale)

    def rewind_signal(self):        
            self.graph1.rewind()
            self.graph2.rewind()

    def clear_signals(self): 
            self.graph1.clear_signal() 
            self.graph2.clear_signal() 
            self.graph3.clear_signal() 

  

    def toggle_play_pause(self): 
            self.graph1.toggle_play_pause() 
            self.graph2.toggle_play_pause() 
            if self.graph1.is_paused: 
                self.play.setIcon(self.play_icon) 
            else: 
                self.play.setIcon(self.pause_icon)
        
    def change_mode(self, index):
            print(index)
            self.clear_signals()

            match index:
                case 0: #uniform
                        self.mode_instance= UniformMode(self.sliders_widget, self.sampling, self.graph2, self.graph3, self.graph1, self.spectrogram_widget2)
                        self.mode_instance.init_mode() 
                        self.mode_instance.reset_sliders_to_default()
                case 1: #musical 
                        self.mode_instance= MusicMode(self.sliders_widget, self.sampling, self.graph2, self.graph3,self.graph1, self.spectrogram_widget2)
                    
                case 2: #animal
                        self.mode_instance= AnimalAndMusic(self.sliders_widget, self.sampling,self.graph2, self.graph3,self.graph1, self.spectrogram_widget2)
                case 3: #ECG
                        
                        self.mode_instance= WeinerFilterr(self.sliders_widget, self.signal.sample_rate, self.graph2, self.graph3, self.graph1, self.spectrogram_widget2,self.graph1.graphWidget,self.signal)
            
          
            # self.spectrogram_input.canvas.figure.clear()
            # self.spectrogram_output.canvas.figure.clear()
            self.clear_signals()
            self.mode_instance.reset_sliders_to_default()
              

            
        
    def set_default(self):
            file_path="Synthetic_1.wav"
            self.mode_instance= UniformMode(self.sliders_widget, self.sampling, self.graph2, self.graph3, self.graph1, self.spectrogram_widget2)
            self.prepare_load(file_path)
            self.mode_instance.init_mode() 
        
            
    def prepare_load(self, file_path):
            self.signal=Signal(3,file_path) 
            if   self.mode_chosen.currentIndex()==3:
                 self.mode_instance.set_signal(self.signal)
            self.sampling.sample_rate= self.signal.sample_rate
            self.sampling.update_sampling(self.graph3, self.signal.signal_data_time, self.signal.signal_data_amplitude,self.sampling.sample_rate)
            if(self.signal.signal_data_amplitude is not None and len(self.signal.signal_data_amplitude) > 0 ):           
                self.sampling.compute_fft(self.signal.signal_data_time,self.signal.signal_data_amplitude)
                self.sampling.plot_frequency_domain(self.sampling.get_frequencies(),self.sampling.get_magnitudes(), False, self.graph3)
            #self.signal=Signal(1,file_path)
            self.spectrogram_input.plot_spectrogram(self.signal.signal_data_amplitude, self.sampling.sample_rate, self.spectrogram_widget1)
            self.spectrogram_output.plot_spectrogram(self.signal.signal_data_amplitude, self.sampling.sample_rate, self.spectrogram_widget2)
            self.mode_instance.set_sample_instance(self.sampling)
            self.mode_instance.set_time(self.signal.signal_data_time)
            self.mode_instance.set_sample_rate(self.signal.sample_rate)
            self.graph1.set_signal(self.signal.signal_data_time, self.signal.signal_data_amplitude) 
            self.graph2.set_signal(self.signal.signal_data_time, self.signal.signal_data_amplitude)
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.set_default()
    sys.exit(app.exec_())