import os
import olefile
import openpyxl

# HWP 텍스트 추출 함수
def extract_text_from_hwp(file_path):
    try:
        if not olefile.isOleFile(file_path):
            return None

        ole = olefile.OleFileIO(file_path)
        if not ole.exists("PrvText"):
            return None

        with ole.openstream("PrvText") as stream:
            content = stream.read().decode("utf-16")
        return content
    except Exception as e:
        print(f"[오류] {file_path} 처리 중 오류 발생: {e}")
        return None

# 엑셀 저장 함수
def save_to_excel(file_texts, output_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "문제 내용"

    ws.append(["파일명", "본문 내용"])

    for file_name, text in file_texts:
        ws.append([file_name, text])

    wb.save(output_path)

# 메인 실행 함수
def convert_hwp_to_excel(folder_path):
    file_texts = []

    for file in os.listdir(folder_path):
        if file.endswith(".hwp"):
            file_path = os.path.join(folder_path, file)
            text = extract_text_from_hwp(file_path)
            if text:
                file_texts.append((file, text))

    if file_texts:
        output_file = os.path.join(folder_path, "기출_문제_모음.xlsx")
        save_to_excel(file_texts, output_file)
        print(f"[완료] {output_file} 로 저장 완료.")
    else:
        print("[알림] 처리할 수 있는 .hwp 파일이 없습니다.")

# 실행
if __name__ == "__main__":
    folder = input("📁 변환할 폴더 경로를 입력하세요: ").strip()
    convert_hwp_to_excel(folder)
