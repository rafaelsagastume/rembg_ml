#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QApplication, QFileDialog, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                             QProgressBar, QPushButton, QScrollArea, QSpinBox,
                             QSplitter, QTabWidget, QVBoxLayout, QWidget)

# Importar funcionalidad existente
from main import process_image


class ImageProcessorThread(QThread):
    """Hilo para procesar imágenes en segundo plano"""
    progress_updated = pyqtSignal(int)
    image_processed = pyqtSignal(str, str)  # Ruta original, ruta procesada
    # Total procesado, total fallido
    processing_finished = pyqtSignal(int, int)
    status_message = pyqtSignal(str)

    def __init__(self, file_list, output_dir, margin):
        super().__init__()
        self.file_list = file_list
        self.output_dir = output_dir
        self.margin = margin
        self.stop_requested = False

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        processed = 0
        failed = 0
        total = len(self.file_list)

        for idx, input_path in enumerate(self.file_list):
            if self.stop_requested:
                break

            self.status_message.emit(f"Procesando: {input_path}")
            result = process_image(input_path, self.output_dir, self.margin)

            if result[1] is not None:  # Si la imagen fue procesada con éxito
                processed += 1
                self.image_processed.emit(input_path, result[1])
            else:
                failed += 1

            # Actualizar progreso
            progress = int((idx + 1) / total * 100)
            self.progress_updated.emit(progress)

        self.processing_finished.emit(processed, failed)

    def stop(self):
        self.stop_requested = True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RemBG - Eliminador de fondos")
        self.resize(1200, 800)

        self.input_files = []
        self.output_dir = os.path.join(os.getcwd(), "output")
        self.processor_thread = None

        self.init_ui()

    def init_ui(self):
        # Widget principal
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Área de control (superior)
        control_group = QGroupBox("Controles")
        control_layout = QVBoxLayout()

        # Primera fila de controles
        file_row = QHBoxLayout()

        # Selección de archivos
        self.select_files_btn = QPushButton("Seleccionar imágenes")
        self.select_files_btn.clicked.connect(self.select_input_files)
        file_row.addWidget(self.select_files_btn)

        # Selección de carpeta
        self.select_folder_btn = QPushButton("Seleccionar carpeta")
        self.select_folder_btn.clicked.connect(self.select_input_folder)
        file_row.addWidget(self.select_folder_btn)

        # Mostrar cantidad de archivos seleccionados
        self.files_label = QLabel("No hay archivos seleccionados")
        file_row.addWidget(self.files_label)

        file_row.addStretch()

        # Selección de carpeta de salida
        self.output_btn = QPushButton("Carpeta de salida")
        self.output_btn.clicked.connect(self.select_output_dir)
        file_row.addWidget(self.output_btn)

        self.output_label = QLabel(self.output_dir)
        file_row.addWidget(self.output_label)

        control_layout.addLayout(file_row)

        # Segunda fila de controles
        options_row = QHBoxLayout()

        # Control de margen
        options_row.addWidget(QLabel("Margen (px):"))
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 100)
        self.margin_spin.setValue(10)
        options_row.addWidget(self.margin_spin)

        options_row.addStretch()

        # Botón para iniciar el procesamiento
        self.process_btn = QPushButton("Procesar imágenes")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        options_row.addWidget(self.process_btn)

        # Botón para detener el procesamiento
        self.stop_btn = QPushButton("Detener")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        options_row.addWidget(self.stop_btn)

        control_layout.addLayout(options_row)

        # Barra de progreso
        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_row.addWidget(self.progress_bar)

        control_layout.addLayout(progress_row)

        # Mensaje de estado
        self.status_label = QLabel("Listo")
        control_layout.addWidget(self.status_label)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # Área para visualizar imágenes (inferior)
        viewer_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo - Imagen original
        original_group = QGroupBox("Imagen original")
        original_layout = QVBoxLayout()
        self.original_image_label = QLabel("No hay imagen seleccionada")
        self.original_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_image_label.setMinimumSize(400, 300)
        original_scroll = QScrollArea()
        original_scroll.setWidget(self.original_image_label)
        original_scroll.setWidgetResizable(True)
        original_layout.addWidget(original_scroll)
        original_group.setLayout(original_layout)

        # Panel derecho - Imagen procesada
        processed_group = QGroupBox("Imagen procesada")
        processed_layout = QVBoxLayout()
        self.processed_image_label = QLabel("No hay imagen procesada")
        self.processed_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processed_image_label.setMinimumSize(400, 300)
        processed_scroll = QScrollArea()
        processed_scroll.setWidget(self.processed_image_label)
        processed_scroll.setWidgetResizable(True)
        processed_layout.addWidget(processed_scroll)
        processed_group.setLayout(processed_layout)

        viewer_splitter.addWidget(original_group)
        viewer_splitter.addWidget(processed_group)

        main_layout.addWidget(viewer_splitter, 1)

    def select_input_files(self):
        """Seleccionar archivos individuales para procesar"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar imágenes",
            "",
            "Imágenes (*.jpg *.jpeg *.png)"
        )

        if files:
            self.input_files = files
            self.files_label.setText(f"{len(files)} archivos seleccionados")
            self.process_btn.setEnabled(True)

            # Mostrar la primera imagen como vista previa
            if files:
                self.display_original_image(files[0])

    def select_input_folder(self):
        """Seleccionar una carpeta para procesar todas sus imágenes"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta con imágenes"
        )

        if folder:
            extensions = ['.jpg', '.jpeg', '.png']
            files = []

            for ext in extensions:
                files.extend([str(p) for p in Path(folder).glob(f"*{ext}")])
                files.extend([str(p)
                             for p in Path(folder).glob(f"*{ext.upper()}")])

            if files:
                self.input_files = files
                self.files_label.setText(
                    f"{len(files)} archivos encontrados en la carpeta")
                self.process_btn.setEnabled(True)

                # Mostrar la primera imagen como vista previa
                self.display_original_image(files[0])
            else:
                self.files_label.setText(
                    "No se encontraron imágenes en la carpeta")
                self.process_btn.setEnabled(False)

    def select_output_dir(self):
        """Seleccionar carpeta de salida para las imágenes procesadas"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de salida",
            self.output_dir
        )

        if folder:
            self.output_dir = folder
            self.output_label.setText(self.output_dir)

    def display_original_image(self, image_path):
        """Mostrar imagen original en el panel izquierdo"""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = self.scale_pixmap(
                pixmap, self.original_image_label.width(), self.original_image_label.height())
            self.original_image_label.setPixmap(pixmap)

    def display_processed_image(self, image_path):
        """Mostrar imagen procesada en el panel derecho"""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = self.scale_pixmap(
                pixmap, self.processed_image_label.width(), self.processed_image_label.height())
            self.processed_image_label.setPixmap(pixmap)

    def scale_pixmap(self, pixmap, target_width, target_height):
        """Escalar un pixmap para que se ajuste al tamaño objetivo manteniendo la proporción"""
        scaled = pixmap.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return scaled

    def start_processing(self):
        """Iniciar el procesamiento de imágenes"""
        if not self.input_files:
            QMessageBox.warning(self, "Error", "No hay imágenes seleccionadas")
            return

        # Deshabilitar botones durante el procesamiento
        self.process_btn.setEnabled(False)
        self.select_files_btn.setEnabled(False)
        self.select_folder_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Iniciar el hilo de procesamiento
        self.processor_thread = ImageProcessorThread(
            self.input_files,
            self.output_dir,
            self.margin_spin.value()
        )

        # Conectar señales
        self.processor_thread.progress_updated.connect(self.update_progress)
        self.processor_thread.image_processed.connect(self.on_image_processed)
        self.processor_thread.processing_finished.connect(
            self.on_processing_finished)
        self.processor_thread.status_message.connect(self.update_status)

        # Iniciar procesamiento
        self.processor_thread.start()

    def stop_processing(self):
        """Detener el procesamiento actual"""
        if self.processor_thread and self.processor_thread.isRunning():
            self.processor_thread.stop()
            self.update_status("Deteniendo procesamiento...")

    def update_progress(self, value):
        """Actualizar la barra de progreso"""
        self.progress_bar.setValue(value)

    def update_status(self, message):
        """Actualizar el mensaje de estado"""
        self.status_label.setText(message)

    def on_image_processed(self, original_path, processed_path):
        """Manejar evento cuando una imagen ha sido procesada"""
        # Mostrar la última imagen procesada
        self.display_original_image(original_path)
        self.display_processed_image(processed_path)

    def on_processing_finished(self, processed, failed):
        """Manejar evento cuando se completa el procesamiento"""
        # Restablecer la interfaz
        self.process_btn.setEnabled(True)
        self.select_files_btn.setEnabled(True)
        self.select_folder_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # Mostrar mensaje de finalización
        self.update_status(
            f"Procesamiento completado: {processed} imágenes exitosas, {failed} fallidas")

        # Mostrar mensaje emergente
        QMessageBox.information(
            self,
            "Procesamiento completado",
            f"Procesamiento completado:\n{processed} imágenes procesadas con éxito\n{failed} imágenes con errores"
        )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
