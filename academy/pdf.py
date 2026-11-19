from io import BytesIO
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from django.conf import settings


fonts=Path(__file__).resolve().parent/'fonts'
pdfmetrics.registerFont(TTFont('LGRegular',str(fonts/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('LGBold',str(fonts/'DejaVuSans-Bold.ttf')))

def fitted_text(pdf,text,x,y,width,max_height,size=24,color='#152a47'):
    for font_size in range(size,10,-1):
        style=ParagraphStyle('fitted',fontName='LGRegular',fontSize=font_size,leading=font_size*1.25,alignment=1,textColor=HexColor(color))
        paragraph=Paragraph(escape(str(text)),style)
        _,height=paragraph.wrap(width,max_height)
        if height<=max_height:
            paragraph.drawOn(pdf,x,y-height);return
    raise ValueError('Certificate text does not fit.')


def render_certificate(certificate):
    combined=hasattr(certificate,'quiz_score')
    buffer=BytesIO();width,height=landscape(A4)
    pdf=canvas.Canvas(buffer,pagesize=(width,height))
    pdf.setTitle('Certificate of Completion - '+certificate.recipient_name)
    pdf.setAuthor(settings.BRAND_NAME)
    pdf.setFillColor(HexColor('#f8fafc'));pdf.rect(0,0,width,height,fill=1,stroke=0)
    pdf.setFillColor(HexColor('#11243e'));pdf.rect(0,height-96,width,96,fill=1,stroke=0)
    pdf.setFillColor(HexColor('#73aef8'));pdf.rect(0,height-100,width,4,fill=1,stroke=0)
    pdf.setStrokeColor(HexColor('#becde0'));pdf.setLineWidth(1);pdf.rect(26,25,width-52,height-50,fill=0,stroke=1)
    pdf.setFont('LGBold',17);pdf.setFillColor(HexColor('#ffffff'));pdf.drawString(48,height-47,settings.BRAND_NAME)
    pdf.setFont('LGRegular',10);pdf.setFillColor(HexColor('#bad0ed'));pdf.drawString(48,height-69,'LEARNING  /  PRACTICE  /  ACHIEVEMENT')
    pdf.setFillColor(HexColor('#42618a'));pdf.setFont('LGRegular',11);pdf.drawCentredString(width/2,456,'CERTIFICATE OF COMPLETION')
    fitted_text(pdf,'This certifies that',70,424,width-140,25,size=15,color='#62748c')
    fitted_text(pdf,certificate.recipient_name,70,390,width-140,72,size=34)
    pdf.setStrokeColor(HexColor('#91b0d6'));pdf.line(170,306,width-170,306)
    fitted_text(pdf,'has completed the quiz and assignment requirements' if combined else 'has successfully passed the assessment',70,290,width-140,25,size=14,color='#62748c')
    fitted_text(pdf,certificate.course_title,85,258,width-170,56,size=23)
    score=certificate.score if combined else certificate.attempt.score
    pdf.setFont('LGRegular',12);pdf.setFillColor(HexColor('#42618a'));pdf.drawCentredString(width/2,178,f'Score: {score}%  |  Issued: {certificate.issued_at:%d %B %Y}')
    if combined:
        pdf.setFont('LGRegular',10);pdf.drawCentredString(width/2,158,f'Quiz: {certificate.quiz_score}% (40%)  |  Assignments: {certificate.assignment_score}% (60%)')
    prefix='/completion' if combined else ''
    url=f'{settings.PUBLIC_BASE_URL}{prefix}/certificates/{certificate.pk}/verify/'
    qr=qrcode.make(url)
    pdf.drawImage(ImageReader(qr.get_image()),width-142,48,88,88)
    pdf.setFont('LGBold',11);pdf.setFillColor(HexColor('#203b5e'));pdf.drawString(52,111,'Digitally verifiable completion record')
    pdf.setFont('LGRegular',9);pdf.setFillColor(HexColor('#62748c'));pdf.drawString(52,90,'Certificate ID: '+str(certificate.pk))
    pdf.drawString(52,73,'Scan the QR code to check current validity, including revocation.')
    pdf.setFont('LGRegular',8);pdf.drawString(52,51,'Issued by the learning platform. Not an accredited degree or professional license.')
    pdf.showPage();pdf.save();return buffer.getvalue()
