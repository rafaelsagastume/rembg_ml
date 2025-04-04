#!/usr/bin/env python3
from rembg import remove
import cv2
import numpy as np
import os
import argparse
from PIL import Image
from pathlib import Path


def process_image(input_path, output_dir, margin=10):
    """
    Procesa una imagen para eliminar el fondo y recortarla al tamaño del objeto

    Args:
        input_path (str): Ruta a la imagen de entrada
        output_dir (str): Directorio donde se guardarán las imágenes procesadas
        margin (int): Margen en píxeles alrededor del producto

    Returns:
        tuple: (ruta_imagen_sin_fondo, ruta_imagen_recortada) o (None, None) en caso de error
    """
    try:
        # Obtener el nombre base del archivo
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)

        # Definir las rutas de salida
        cropped_output_path = os.path.join(output_dir, f"{name}.png")

        print(f"Procesando: {input_path}")

        # Proceso con rembg
        with open(input_path, 'rb') as i:
            input_data = i.read()

            # Usar rembg para eliminar el fondo
            output = remove(input_data)

        # Recortar la imagen para que esté cerca del producto
        # Cargar la imagen con fondo transparente
        img_array = np.frombuffer(output, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

        # Extraer el canal alfa (transparencia)
        alpha_channel = img[:, :, 3]

        # Encontrar los píxeles no transparentes (donde el producto está)
        y_indices, x_indices = np.where(alpha_channel > 0)

        if len(x_indices) > 0 and len(y_indices) > 0:
            # Encontrar los límites del producto
            x_min, x_max = np.min(x_indices), np.max(x_indices)
            y_min, y_max = np.min(y_indices), np.max(y_indices)

            # Añadir el margen, asegurándose de no salirse de los límites de la imagen
            x_min = max(0, x_min - margin)
            y_min = max(0, y_min - margin)
            x_max = min(img.shape[1] - 1, x_max + margin)
            y_max = min(img.shape[0] - 1, y_max + margin)

            # Recortar la imagen
            cropped_img = img[y_min:y_max+1, x_min:x_max+1]

            # Guardar la imagen recortada
            cv2.imwrite(cropped_output_path, cropped_img)
            print(f"  ✓ Imagen recortada guardada como: {cropped_output_path}")

            # Dimensiones antes y después
            print(f"  ✓ Dimensiones originales: {img.shape[1]}x{img.shape[0]}")
            print(
                f"  ✓ Dimensiones después del recorte: {cropped_img.shape[1]}x{cropped_img.shape[0]}")
            return None, cropped_output_path
        else:
            print("  ✗ No se encontraron píxeles no transparentes en la imagen")
            return None, None

    except Exception as e:
        print(f"  ✗ Error al procesar la imagen: {e}")
        return None, None


def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(
        description='Elimina el fondo y recorta imágenes en lote')
    parser.add_argument(
        'input_dir', help='Directorio que contiene las imágenes a procesar')
    parser.add_argument(
        '-o', '--output-dir', help='Directorio donde se guardarán las imágenes procesadas', default='output')
    parser.add_argument('-m', '--margin', type=int,
                        help='Margen en píxeles alrededor del producto', default=10)
    parser.add_argument(
        '-e', '--extensions', help='Extensiones de archivo a procesar (separadas por coma)', default='jpg,jpeg,png')

    args = parser.parse_args()

    # Verificar que el directorio de entrada existe
    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print(f"Error: El directorio de entrada {input_dir} no existe")
        return

    # Crear el directorio de salida si no existe
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    print(f"Las imágenes procesadas se guardarán en: {output_dir}")

    # Convertir extensiones a lista y agregar el punto
    extensions = [
        f".{ext.lower().strip('.')}" for ext in args.extensions.split(',')]

    # Contar el número total de imágenes a procesar
    total_images = 0
    processed_images = 0
    failed_images = 0

    for extension in extensions:
        total_images += len(list(Path(input_dir).glob(f"*{extension}")))

    print(
        f"Encontradas {total_images} imágenes con extensiones: {', '.join(extensions)}")

    # Procesar cada imagen en el directorio
    for extension in extensions:
        for input_path in Path(input_dir).glob(f"*{extension}"):
            result = process_image(str(input_path), output_dir, args.margin)

            if result[0] is not None:
                processed_images += 1
            else:
                failed_images += 1

            print("-" * 40)  # Separador entre imágenes

    # Mostrar resumen
    print("\nResumen:")
    print(f"Total de imágenes: {total_images}")
    print(f"Imágenes procesadas correctamente: {processed_images}")
    print(f"Imágenes con errores: {failed_images}")


if __name__ == "__main__":
    main()
