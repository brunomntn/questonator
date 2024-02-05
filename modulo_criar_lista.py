import os
from config import nomeLista, aceitarDiscursivas, apenasDiscursivas
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from PIL import Image



def resize_imagem(image, width):
    w_percent = (width / float(image.width))
    h_size = int((float(image.height) * float(w_percent)))
    return image.resize((width, h_size), Image.Resampling.LANCZOS)


def juntar_imagens(image1, image2):
    new_width = image1.width + image2.width
    new_height = max(image1.height, image2.height)

    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    new_image.paste(image1, (0, 0))
    new_image.paste(image2, (image1.width, 0))
    return new_image

def juntar_com_texto(image1, image2, image3):
    new_width = image2.width + max(image1.width, image3.width)
    new_height = max(image2.height, image1.height+image3.height)
    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    new_image.paste(image2, (0,0))
    new_image.paste(image3, (image2.width, 0))
    new_image.paste(image1, (image2.width, image3.height))
    return new_image


def criar_pdf(discursivas, comErro, solucoes):
    print("PROCESSANDO IMAGENS...")
    source_folder = "imagens_extraidas_2"

    destination_folder = "imagens_modificadas_2"

    default_width = 794  

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    for folder_name in os.listdir(source_folder):
        folder_path = os.path.join(source_folder, folder_name)

        if os.path.isdir(folder_path):
            images = os.listdir(folder_path)
            if len(images) == 1:
                image_path = os.path.join(folder_path, images[0])
                try:
                    with Image.open(image_path) as img:
                        img = resize_imagem(img, default_width)
                        img.save(os.path.join(destination_folder, f"{folder_name}.png"))
                except Exception:
                    image = Image.new(mode='RGBA', size=(default_width, 10))
                    image.save(os.path.join(destination_folder, f"{folder_name}.png"))
            elif len(images) == 2:
                image1_path = os.path.join(folder_path, images[0])
                image2_path = os.path.join(folder_path, images[1])
                try:
                    with Image.open(image1_path) as img1, Image.open(image2_path) as img2:
                        merged_img = juntar_imagens(img1, img2)
                        merged_img = resize_imagem(merged_img, default_width)
                        merged_img.save(os.path.join(destination_folder, f"{folder_name}.png"))
                except Exception:
                    image = Image.new(mode='RGBA', size=(default_width, 10))
                    image.save(os.path.join(destination_folder, f"{folder_name}.png"))
            elif len(images) == 3:
                image1_path = os.path.join(folder_path, images[0])
                image2_path = os.path.join(folder_path, images[1])
                image3_path = os.path.join(folder_path, images[2])
                try:
                    with Image.open(image1_path) as img1, Image.open(image2_path) as img2, Image.open(image3_path) as img3:
                        merged_img = juntar_com_texto(img1, img2, img3)
                        merged_img = resize_imagem(merged_img, default_width)
                        merged_img.save(os.path.join(destination_folder, f"{folder_name}.png"))
                except Exception:
                    image = Image.new(mode='RGBA', size=(default_width, 10))
                    image.save(os.path.join(destination_folder, f"{folder_name}.png"))
    print("IMAGENS PROCESSADAS")

    image_files = sorted(os.listdir(destination_folder), key=lambda x: int(x.split('.')[0]))

    pdf_file = nomeLista

    c = canvas.Canvas(pdf_file, pagesize=A4)
    line_height = 18 
    current_page_height = A4[1]
    y_position = current_page_height - 24

    number = 0
    for i, image_file in enumerate(image_files, start=1):

        if not apenasDiscursivas:
            if i not in comErro:
                if not aceitarDiscursivas:
                    if i in discursivas:
                        number +=1
                        continue  
            else:
                number +=1
                continue       
        else:
            if i in comErro or i not in discursivas:
                number +=1
                continue
                
                
            image_path = os.path.join(destination_folder, image_file)
            
            img = Image.open(image_path)
            width, height = img.size
            width = width / 1.6
            height = height / 1.7
            
            if y_position - (height + line_height) < 24:
                c.showPage()
                current_page_height = A4[1]
                y_position = current_page_height - 24
            
            x = ((A4[0] - width) / 2) - 10
            y = y_position - height
            
            number_x = 5  
            number_y = y_position - 25  
            
            c.drawImage(image_path, x, y, width=width, height=height, mask='auto')
            c.setFont("Helvetica-Bold", 20) 
            c.drawString(number_x, number_y, str(i-number))
            c.line(x, y - line_height, x + width*2, y - line_height)
            y_position = y - 25


    c.showPage()

    if not apenasDiscursivas:
        num_colunas = 2 

        coluna_largura = A4[0] / num_colunas
        row_altura = 22

        data = [[solucoes[i]] for i in range(len(solucoes))]

        rows_por_coluna = (len(data) + num_colunas - 1) // num_colunas 

        dados_coluna = []

        for i in range(num_colunas):
            start_idx = i * rows_por_coluna
            end_idx = min(start_idx + rows_por_coluna, len(data))
            dados_coluna.append(data[start_idx:end_idx])

        x_coordenadas = [0, A4[0] / num_colunas]

        for i, dados_coluna in enumerate(dados_coluna):
            table = Table(dados_coluna, colWidths=[coluna_largura], rowHeights=[row_altura] * len(dados_coluna))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            table.wrapOn(c, 0, 0)
            table.drawOn(c, x_coordenadas[i], A4[1] - row_altura * len(dados_coluna))
        
        c.showPage()
    c.save()
    
    print(f"LISTA CRIADA COM SUCESSO")