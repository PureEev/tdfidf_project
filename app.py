import os
import math
import re
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret_key"

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt'}


def allowed_file(filename):
    """Проверяем расширение файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_text(text):
    """Приводит текст к нижнему регистру и удаляет лишние символы."""
    text = text.lower()
    text = re.sub(r"[^a-zа-яё0-9\s]", " ", text)
    return text


def split_into_documents(text):
    """
    Разбивает текст на документы.
    Если есть пустые строки, считаем, что разделителем является два и более переводов строки.
    Если текст не содержит пустых строк, то рассматриваем весь текст как один документ.
    """
    docs = [doc.strip() for doc in text.split("\n\n") if doc.strip()]
    if not docs:
        docs = [text.strip()]
    return docs


def compute_tf_idf(text):
    """
    Вычисляет tf для каждого слова и idf по документам.
    Возвращает список кортежей (слово, tf, idf), отсортированных по убыванию idf.
    """
    text = clean_text(text)
    documents = split_into_documents(text)
    total_docs = len(documents)

    words_all = text.split()
    tf_counter = Counter(words_all)

    df_counter = Counter()
    for doc in documents:
        words = set(doc.split())
        for word in words:
            df_counter[word] += 1

    tf_idf_data = []
    for word, tf in tf_counter.items():
        df = df_counter.get(word, 0)
        idf = math.log(total_docs / (df + 1))
        tf_idf_data.append((word, tf, idf))

    tf_idf_data.sort(key=lambda x: x[2], reverse=True)
    return tf_idf_data[:50]


@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Файл не выбран")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("Файл не выбран")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                flash("Ошибка при чтении файла. Убедитесь, что файл имеет кодировку utf-8.")
                return redirect(request.url)

            results = compute_tf_idf(text)
            flash(f"Файл '{filename}' успешно загружен и обработан.")

    return render_template("index.html", results=results)


@app.route('/documents')
def documents():
    """
    Отображает список всех загруженных документов,
    позволяет скачать или удалить их.
    """
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template("documents.html", files=files)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Отдает файл из директории uploads для скачивания или просмотра."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Удаляет выбранный файл."""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Файл '{filename}' был удалён.")
    else:
        flash(f"Файл '{filename}' не найден.")
    return redirect(url_for('documents'))


if __name__ == '__main__':
    app.run(debug=True)
