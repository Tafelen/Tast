import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
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

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon32.ico')

# 単語セット
kanji_question2 = {
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
    "キンコ五年の判決を下す。": "禁錮"
    }

kanji_question3 = {
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

kanji_question4 = {
    "鉛筆のシンの材料を調べる。": "芯",
    "カセイに苦しむ国民。": "苛政",
    "手足の筋肉がイシュクする。": "萎縮",
    "気持ちがナえる。": "萎",
    "心のカットウを描いた文学。": "葛藤",
    "ズガイコツに入ったひび。": "頭蓋骨",
    "戦いのヒブタが切られる。": "火蓋",
    "サゲスむような視線。": "蔑",
    "ケイベツに値する行為だ。": "軽蔑",
    "証拠のインペイを図る。": "隠蔽",
    "フジの花が咲く。": "藤",
    "アイイロに染められた布。": "藍色",
    "見事なサイハイだった。": "采配",
    "壁画が発見されたドウクツ。": "洞窟",
    "聴衆からバセイが飛ぶ。": "罵声",
    "医師からショホウセンをもらう。": "処方箋",
    "サイバシは「箸」と数えない。": "菜箸",
    "窓辺にトリカゴをつるす。": "鳥籠",
    "コケツに入るような危険を冒す。": "虎穴",
    "センチャの入れ方にこだわる。": "煎茶",
    "波にホンロウされる小舟。": "翻弄",
    "エンコンによる犯行。": "怨恨",
    "死者のオンネンを晴らす。": "怨念",
    "シイ的な判断にすぎない。": "恣意",
    "何とかコンセキをとどめる。": "痕跡",
    "ヤせた土地でもよく育つ。": "痩",
}

kanji_question5 = {
    "胃にカイヨウができたようだ。": "潰瘍",
    "メジリにしわを寄せて笑う。": "目尻",
    "鮎が川をソジョウする。": "遡上",
    "十年前まで記憶をサカノボる。": "遡",
    "ケンソンして何も言わない。": "謙遜",
    "小麦粉を使ったメンルイ。": "麺類",
    "コウバイの急な坂をのぼる。": "勾配",
    "生活のニオいを感じない。": "匂",
    "山はクラヤミに包まれていた。": "暗闇",
    "団子のクシザしを頑張る。": "串刺",
    "テンドンを二人前注文する。": "天丼",
    "イノチゴいを聞き入れる。": "命乞",
    "ひとフロ浴びる。": "風呂",
    "自然のヨウサイに囲まれた地。": "要塞",
    "ヘイソク状況を打破する。": "閉塞",
    "自然に囲まれてソウカイだ。": "爽快",
    "ダンガイ絶壁の上に立つ。": "断崖",
    "ガケ崩れの対策を行う。": "崖",
    "スナアラシの中から救出する。": "砂嵐",
    "掃除はゾウキンがけが一番。": "雑巾",
    "ゴイの豊富な人。": "語彙",
    "ケンポウを護身用に習う。": "拳法",
    "シンシな態度に好感をもつ。": "真摯",
    "赤いハンテンが見られる。": "斑点",
    "一年の計はガンタンにあり。": "元旦",
    "ソウゾフの代から営む。": "曽祖父"
}

kanji_question6 = {
    "富士サンロクの自然を撮る。": "山麓",
    "台風が残した大きなツメアト。": "爪痕",
    "ツマサキをそろえて立つ" : "爪先",
    "昔から珍重されたゾウゲ。": "象牙",
    "カンペキな演技を見せた選手。": "完璧",
    "汚職事件で政権がガカイする。": "瓦解",
    "赤いカワラの屋根が並ぶ。": "瓦",
    "自然へのイケイの念を抱く。": "畏敬",
    "キンキ地方の拠点となる。": "近畿",
    "ミケンのしわ。": "眉間",
    "不快そうにマユネを寄せる。": "眉根",
    "セキズイ損傷と診断される。": "脊髄",
    "ジンゾウを摘出する手術。": "腎臓",
    "シュウチ心に見舞われる。": "羞恥",
    "人もウラヤむ夫婦仲だ。": "羨",
    "センボウのまなざし。": "羨望",
    "肌のイロツヤがよい。": "色艶",
    "ハチミツは栄養価が高い。": "蜂蜜",
    "ダッキュウ予防のトレーニング。": "脱臼",
    "ドンヨクに知識を吸収する。": "貪欲",
    "批評はシンラツをきわめた。": "辛辣",
    "チャガマは茶道具の一種だ。": "茶釜",
    "今後を考えるとユウウツだ。": "憂鬱",
    "カンコクゴを流ちょうに話す。": "韓国語",
    "願いをこめセンバヅルを折る。": "千羽鶴",
    "二人の間にキレツが入る": "亀裂"
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
}


@app.route('/kanji2')
def kanji2():
    global question_num, correct_num, incorrect_num
    question_num = 1
    correct_num = 0
    incorrect_num = 0
    session.clear()
    if not session.get('initialized'):
        init_quiz_state2()
    return redirect(url_for('kanji_check', quiz_type='kanji2'))

def init_quiz_state2():
    """クイズの状態を初期化する関数"""
    session['initialized'] = True
    session['question_num'] = 1
    session['correct_num'] = 0
    session['incorrect_num'] = 0
    session['kanji_questions'] = kanji_question2.copy()


@app.route('/kanji3')
def kanji3():
    global question_num, correct_num, incorrect_num
    question_num = 1
    correct_num = 0
    incorrect_num = 0
    session.clear()
    if not session.get('initialized'):
        init_quiz_state3()
    return redirect(url_for('kanji_check', quiz_type='kanji3'))

def init_quiz_state3():
    """クイズの状態を初期化する関数"""
    session['initialized'] = True
    session['question_num'] = 1
    session['correct_num'] = 0
    session['incorrect_num'] = 0
    session['kanji_questions'] = kanji_question3.copy()
    
@app.route('/kanji4')
def kanji4():
    global question_num, correct_num, incorrect_num
    question_num = 1
    correct_num = 0
    incorrect_num = 0
    session.clear()
    if not session.get('initialized'):
        init_quiz_state4()
    return redirect(url_for('kanji_check', quiz_type='kanji4'))

def init_quiz_state4():
    """クイズの状態を初期化する関数"""
    session['initialized'] = True
    session['question_num'] = 1
    session['correct_num'] = 0
    session['incorrect_num'] = 0
    session['kanji_questions'] = kanji_question4.copy()
    

@app.route('/kanji5')
def kanji5():
    global question_num, correct_num, incorrect_num
    question_num = 1
    correct_num = 0
    incorrect_num = 0
    session.clear()
    if not session.get('initialized'):
        init_quiz_state5()
    return redirect(url_for('kanji_check', quiz_type='kanji5'))

def init_quiz_state5():
    """クイズの状態を初期化する関数"""
    session['initialized'] = True
    session['question_num'] = 1
    session['correct_num'] = 0
    session['incorrect_num'] = 0
    session['kanji_questions'] = kanji_question5.copy()
    
@app.route('/kanji6')
def kanji6():
    global question_num, correct_num, incorrect_num
    question_num = 1
    correct_num = 0
    incorrect_num = 0
    session.clear()
    if not session.get('initialized'):
        init_quiz_state6()
    return redirect(url_for('kanji_check', quiz_type='kanji6'))

def init_quiz_state6():
    """クイズの状態を初期化する関数"""
    session['initialized'] = True
    session['question_num'] = 1
    session['correct_num'] = 0
    session['incorrect_num'] = 0
    session['kanji_questions'] = kanji_question6.copy()


@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/kanji_check', methods=['GET', 'POST'])
def kanji_check():
    quiz_type = request.args.get('quiz_type', 'kanji')
    
    if quiz_type == 'kanji' and not session.get('initialized'):
        return redirect(url_for('kanji'))
    elif quiz_type == 'kanji2' and not session.get('initialized'):
        return redirect(url_for('kanji2'))
    elif quiz_type == 'kanji3' and not session.get('initialized'):
        return redirect(url_for('kanji3'))
    elif quiz_type == 'kanji4' and not session.get('initialized'):
        return redirect(url_for('kanji4'))
    elif quiz_type == 'kanji5' and not session.get('initialized'):
        return redirect(url_for('kanji5'))
    elif quiz_type == 'kanji6' and not session.get('initialized'):
        return redirect(url_for('kanji6'))
    if 'question_num' not in session:
        if quiz_type == 'kanji':
            return redirect(url_for('kanji'))
        elif quiz_type == 'kanji2':
            return redirect(url_for('kanji2'))
        elif quiz_type == 'kanji3':
            return redirect(url_for('kanji3'))
        elif quiz_type == 'kanji4':
            return redirect(url_for('kanji4'))
        elif quiz_type == 'kanji5':
            return redirect(url_for('kanji5'))
        elif quiz_type == 'kanji6':
            return redirect(url_for('kanji6'))
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
            model = genai.GenerativeModel('models/gemini-2.0-flash')
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