import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai
from flask_cors import CORS
import markdown
import random
import secrets
# from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# AIの設定
load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("APIキーが設定されていません。.envファイルを確認してください。")
genai.configure(api_key=API_KEY)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
]
# 生成設定
generation_config = {
    'temperature': 0.7,
    'top_k': 25,
    'top_p': 0.9,
    'max_output_tokens': 1500
}




@app.route("/")
def index():
    return render_template("home.html")

@app.route("/select")
def select():
    return render_template("select.html")

@app.route("/kanji")
def kanji():
    global question_num, correct_num, incorrect_num
    question_num = 1
    correct_num = 0
    incorrect_num = 0
    session.clear()
    if not session.get('initialized'):
        init_quiz_state()
    return redirect(url_for('kanji_check'))

def init_quiz_state():
    """クイズの状態を初期化する関数"""
    session['initialized'] = True
    session['question_num'] = 1
    session['correct_num'] = 0
    session['incorrect_num'] = 0
    session['kanji_questions'] = {
        "ゐる": "すわる/連れる",
    "ぐす": "備わる/備える",
    "いそぐ": "準備する",
    "まうく": "用意する",
    "やる": "行かせる/送る",
    "おこす": "送ってくる/よこす",
    "およすく": "成長する",
    "ねぶ": "おとなびる",
    "よろし": "適当だ",
    "わろし": "よくない",
    "あし": "悪い/へただ",
    "をかし": "興趣がある",
    "あはれ": "ああ/しみじみとした情趣",
    "おもしろし": "趣がある",
    "はかなし": "頼りない"
    }

# kanji_question_dict = {
#     "彼女は音楽を「きく」": "彼女は音楽を聴く",
#     "試合の「けっか」を待つ": "試合の結果を待つ",
#     "交通事故を「ふせぐ」": "交通事故を防ぐ",
#     "「たいりょく」が不足している": "体力が不足している",
#     "新しい「じだい」に生きる": "新しい時代に生きる"
#     }


@app.route('/kanji_check', methods=['GET', 'POST'])
def kanji_check():
    if not session.get('initialized'):
        return redirect(url_for('kanji'))
    
    if 'question_num' not in session:
        return redirect(url_for('kanji'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == '答えを見る':
            session['answer_shown'] = True

        elif action == '次へ':
            selected_choice = request.form.get('answer_option')
            if selected_choice == 'correct':
                session['correct_num'] += 1
            elif selected_choice == 'incorrect':
                session['incorrect_num'] += 1

            if not session['kanji_questions']:
                return redirect(url_for('result'))

            # 次の問題を選択
            keys = list(session['kanji_questions'].keys())
            random_key = random.choice(keys)
            session['current_question'] = random_key
            session['current_answer'] = session['kanji_questions'][random_key]
            del session['kanji_questions'][random_key]
            session['answer_shown'] = False
            session['question_num'] += 1

    elif request.method == 'GET':
        if not session.get('current_question'):
            if not session.get('kanji_questions'):
                return redirect(url_for('result'))
            
            keys = list(session['kanji_questions'].keys())
            random_key = random.choice(keys)
            session['current_question'] = random_key
            session['current_answer'] = session['kanji_questions'][random_key]
            del session['kanji_questions'][random_key]
            session['answer_shown'] = False

    return render_template('kanji.html',
                        question_num=session['question_num'],
                        question=session.get('current_question', ''),
                        answer=session.get('current_answer', '--') if session.get('answer_shown', False) else '--',
                        answer_shown=session.get('answer_shown', False))

# ここからは質問AI
@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        user_question = request.form["user_question"]
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            response = model.generate_content(user_question)
            generated_text = response.text
        except Exception as e:
            generated_text = f"おぉっと…エラーが発生したようだよぉ。。。エラーコードはこれだよ：{e}"
        # 共通の処理としてマークダウン変換を行う
        markdown_text = generated_text
        generated_html = markdown.markdown(markdown_text)
        return render_template("ai.html", question=user_question, response=generated_html)
    else:
        return render_template("ai.html")
    
@app.route('/result')
def result():
    if not session.get('initialized'):
        return redirect(url_for('kanji'))
    
    # 結果表示後はセッションをクリアしない
    return render_template('result.html', 
                        correct_num=session.get('correct_num', 0), 
                        incorrect_num=session.get('incorrect_num', 0))
    
if __name__ == "__main__":
    app.run(debug=True)
# , host="10.75.163.249", port=80