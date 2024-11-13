from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from decimal import Decimal

app = Flask(__name__)

# Fonction pour convertir Decimal en float
def convert_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value

# Fonction pour créer un watermark avec un angle dynamique en fonction de l'orientation
def create_watermark(text, page_size):
    buffer = BytesIO()
    
    # Convertir la taille de la page en float
    width, height = map(convert_to_float, page_size)
    
    # Détecter l'orientation de la page (landscape ou portrait)
    if width > height:
        angle = 35  # Landscape
    else:
        angle = 55  # Portrait

    # Créer un canvas pour dessiner le watermark
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    # Enregistrer l'état du canvas avant transformation
    c.saveState()
    
    # Appliquer une rotation en fonction de l'orientation
    c.translate(width / 2, height / 2)  # Déplacer l'origine au centre
    c.rotate(angle)  # Rotation selon l'angle détecté (35 ou 55 degrés)

    # Ajouter le texte du watermark après la rotation
    c.setFont("Helvetica", 30)
    c.setFillColorRGB(0.6, 0.6, 0.6, alpha=0.3)  # Couleur grise avec transparence
    c.drawCentredString(0, 0, text)  # Dessiner le texte au centre (après translation)
    
    # Restaurer l'état initial du canvas
    c.restoreState()
    
    # Sauvegarder le PDF dans le buffer
    c.save()
    buffer.seek(0)
    return buffer

# Fonction pour ajouter le watermark à un PDF
def add_watermark(input_pdf, watermark_text):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Pour chaque page du PDF d'origine, ajouter le watermark
    for page in reader.pages:
        page_size = page.mediabox.upper_right
        page_size = (convert_to_float(page_size[0]), convert_to_float(page_size[1]))

        # Créer un watermark en tant que PDF avec rotation dynamique
        watermark_pdf = create_watermark(watermark_text, page_size)
        watermark_reader = PdfReader(watermark_pdf)
        watermark_page = watermark_reader.pages[0]
        
        # Fusionner la page avec le watermark
        page.merge_page(watermark_page)
        writer.add_page(page)

    # Sauvegarde dans un fichier en mémoire
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    
    return output_pdf

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    file = request.files['file']
    watermark_text = request.form['watermark']
    
    # Ajouter le watermark
    output_pdf = add_watermark(file, watermark_text)
    
    # Retourner le PDF modifié
    return send_file(output_pdf, as_attachment=True, download_name='watermarked.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
