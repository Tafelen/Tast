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
    "オウセイな知識欲を持つ": "旺盛",
    "読書ザンマイの生活を送る": "三昧",
    "責任の所在がアイマイだ": "曖昧",
    "カタヒジ張らずに楽しむ": "肩肘",
    "コカンセツが外れやすい": "股関節",
    "ウチマタすかしの技": "内股",
    "リョウワキに荷物を抱える": "両脇",
    "がんは悪性シュヨウをさす": "腫瘍",
    "どうにもルイセンがゆるい": "涙腺",
    "ヒザガシラをつき合わせる": "膝頭",
    "客室ごとにハイゼンする": "配膳",
    "お見合いのおゼンダて": "膳立",
    "オクビョウ風に吹かれる": "臆病",
    "息子をマクラモトに呼ぶ": "枕元",
    "家の周りにテッサクを巡らす": "鉄柵",
    "ケタ違いの強さを見せた": "桁",
    "心筋コウソクの発作が出る": "梗塞",
    "大臣のイスを争う": "椅子",
    "魚はセキツイを持つ生物だ": "脊椎",
    "社員のシンボクを図る": "親睦",
    "人形ジョウルリが伝わる": "浄瑠璃",
    "知育ガングのカタログ": "玩具",
    "カイショを基礎から学ぶ": "楷書",
    "意識がメイリョウではない": "明瞭",
    "ドウコウが開いた状態になる": "瞳孔",
    "シブガキを干して食用にする": "渋柿",
    "剣道のケイコに励む日々。": "稽古",
    "ハンソデのシャツを羽織る。": "半袖",
    "活動のスソノを広げる。": "裾野",
    "国の経済がハタンしそうだった。": "破綻",
    "皆でチミツに練った計画。": "綿密",
    "船がウゲンに大きく傾く。": "右舷",
    "ニジイロに輝く宝石の数々。": "虹色",
    "師のフホウに愕然とする。": "訃報",
    "悪政に対する民衆のホウキ。": "蜂起",
    "伊勢神宮へハツモウデに行く。": "初詣",
    "他人のことをセンサクするな。": "詮索",
    "ダレカレなしに声をかける。": "誰彼",
    "ハイカイを芸術に高めた芭蕉。": "俳諧",
    "人間洞察とテイカンがある。": "諦観",
    "ナゾ解きを披露する。": "謎",
    "封筒に切手をチョウフする。": "貼付",
    "ハリ絵での年賀状を作る。": "貼",
    "決してワイロを渡さなかった。": "賄賂",
    "大きなカケに出る。": "賭",
    "なぜかシッソウしたか不明だ。": "失踪",
    "相手チームにイッシュウされた。": "一蹴",
    "ショウチュウの醸造が盛んだ。": "焼酎",
    "昏睡状態からカクセイする。": "覚醒",
    "都市はヘンボウし続ける。": "変貌",
    "キンシュウの候という時候の挨拶。": "錦秋",
    "キンコ五年の判決を下す。": "禁錮",
    "ピアノのケンバンをたたく。": "鍵盤",
    "事件を解くカギを握る。": "鍵",
    "ナベリョウリが名物の旅館。": "鍋料理",
    "カマクラ時代に勢力をふるう。": "鎌倉",
    "金魚にエサをやる。": "餌",
    "彼の計画はガベイに帰した。": "画餅",
    "持ちゴマが多いチーム。": "駒",
    "制度がケイガイ化していく。": "形骸",
    "衝突したセツナ、気を失う。": "刹那",
    "医師の資格をハクダツされる。": "剥奪",
    "塗装がハがれる。": "剥",
    "太平洋戦争がボッパツする。": "勃発",
    "遠くのシンセキより近くの他人。": "親戚",
    "ありがたくチョウダイします。": "頂戴",
    "国王のタイカン式。": "戴冠",
    "店の大ダンナに仕える。": "旦那",
    "ザンシンなアイデアを出す。": "斬新",
    "名誉キソンで訴えられる。": "毀損",
    "ヒゴロの感謝を伝える。": "日頃",
    "合格のためのヒッス条件。": "必須",
    "きれいにセイトンされた部屋。": "整頓",
    "誰もいない間にホオ張る。": "頬",
    "ガクカンセツを痛める。": "顎関節",
    "コース前半でアゴを出した。": "顎",
    "メイオウセイは準惑星とされる。": "冥王星",
    "アテサキ不明で戻ってきた。": "宛先",
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

@app.route('/bulletin')
def bulletin():
    return render_template('404.html')

@app.route('/contact')
def contact():
    return render_template('404.html')

    
if __name__ == "__main__":
    app.run(debug=True)
# , host="10.75.163.249", port=80