import os
import re
import pdfplumber
from openpyxl import Workbook

def extract_ordered_text_from_pdf(pdf_path):
    all_questions = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            width = page.width
            height = page.height
            mid_x = width / 2

            # 왼쪽/오른쪽 영역 분리
            left = page.within_bbox((0, 0, mid_x, height))
            right = page.within_bbox((mid_x, 0, width, height))

            # 텍스트 추출
            left_text = left.extract_text() if left else ''
            right_text = right.extract_text() if right else ''

            combined_text = (left_text or '') + '\n' + (right_text or '')
            all_questions.append(combined_text)

    return '\n'.join(all_questions)

def split_questions(text):
    # "1.", "2.", 또는 "1번", "2번" 등을 기준으로 문항 구분
    pattern = r"(?:(?<=\n)|^)(\d{1,3}[.번])[\s\S]*?(?=(?:\n\d{1,3}[.번])|$)"
    matches = re.findall(pattern, text)

    if not matches:
        # 백업: 줄 기준으로 반환
        return text.split('\n')

    # re.findall 위 패턴은 번호만 반환하므로 re.finditer로 본문 가져오기
    matches = re.finditer(r"(?:(?<=\n)|^)(\d{1,3}[.번])([\s\S]*?)(?=(?:\n\d{1,3}[.번])|$)", text)
    questions = []
    for m in matches:
        number = m.group(1)
        body = m.group(2).strip()
        questions.append(f"{number} {body}")
    return questions

def save_to_excel(questions, output_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "문항 정리"

    for i, q in enumerate(questions, start=1):
        ws.cell(row=i, column=1, value=q)

    wb.save(output_path)

def convert_pdf_folder_to_excel(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            raw_text = extract_ordered_text_from_pdf(pdf_path)
            questions = split_questions(raw_text)

            output_filename = os.path.splitext(filename)[0] + ".xlsx"
            output_path = os.path.join(folder_path, output_filename)

            save_to_excel(questions, output_path)
            print(f"[완료] {output_filename} 생성됨")

# 실행
if __name__ == "__main__":
    folder = input("📁 변환할 PDF 폴더 경로를 입력하세요: ").strip()
    convert_pdf_folder_to_excel(folder)
