# Twitter APIを利用する際に必要なWeb API
import tweepy
# 取得したツイートを前処理するライブラリ
import pandas as pd
# flaskのライブラリを全部入れる
from flask import Flask, render_template, request, logging, Response, redirect, flash
# configはconfig.pyで設定したTwitterの認証情報が入っているライブラリ
from config import CONFIG

# 各種ツイッターのキーをセット
CONSUMER_KEY = CONFIG["CONSUMER_KEY"]
CONSUMER_SECRET = CONFIG["CONSUMER_SECRET"]
ACCESS_TOKEN = CONFIG["ACCESS_TOKEN"]
ACCESS_SECRET = CONFIG["ACCESS_SECRET"]

# Tweepyを利用するために認証情報を入れる
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

# Tweepyの認証情報をもとにAPIが利用できるインスタンスを作成
api = tweepy.API(auth)

# flaskの起動。flaskを初期化してインスタンスを作成
# appから各種flaskのメソッドを呼ぶ出すことができる
app = Flask(__name__)

# ツイッターからとるデータを設定。ツイートのID(tweet_id)、ツイートした日(created_at)、ツイート内容(text)、いいね数(fav)、リツイート数(retweets)をリスト形式で設定しています。これはのちほど使う変数
# Viewの処理
columns = [
   "tweet_id",
   "created_at",
   "text",
   "fav",
   "retweets"
   ]

# hoge.comにアクセスした時に、実行される関数
@app.route('/', methods = ["GET" , "POST"])
def index():
	# HTTPのPOSTリクエストが送られた時を条件
	if request.method == 'POST':
		# HTMLから受け取った値を、python上で取得
		user_id = request.form['user_id'] # formの「name="user_id"」を取得
		tweets_df = get_tweets_df(user_id) # PandasのDataFrame形式でツイートを取得
		grouped_df = get_grouped_df(tweets_df) # DataFrame形式で取得したツイートをget_grouped_df関数で日時集計を取得
		sorted_df = get_sorted_df(tweets_df) # 日時順にツイートを並べるget_sorted_df関数
		return render_template(
								'index.html',
								profile = get_profile(user_id), # ユーザーのプロフィールを取得するget_profile関数を呼び出す
								tweets_df = tweets_df,
								grouped_df = grouped_df,
								sorted_df = sorted_df
								)
	else:
		return render_template('index.html')

def get_tweets_df(user_id):
	tweets_df = pd.DataFrame(columns=columns) # Pandasのデータフレームオブジェクトを上で指定した列名でリスト作成
	for tweet in tweepy.Cursor(api.user_timeline, screen_name = user_id, exclude_replies = True).items(): # ツイッターAPIを利用してユーザーのツイートを取得。exclude_replies = Trueはリプライを除く設定。これをfor文で回して全てのツイートを取得
		try:
			if not "RT @" in tweet.text: # ツイートの内容に@が入っていない場合のみ、ツイートを取得できるようにしている
				# ツイーターのAPIから取得したそれぞれの値をPandasのSeries形式で取得
				se = pd.Series([
					tweet.id,
					tweet.created_at,
					tweet.text.replace('\n', ''),
					tweet.favorite_count,
					tweet.retweet_count
					]
					,columns
					)
				tweets_df = tweets_df.append(se, ignore_index=True) # tweets_dfに行を追加している
		except Exception as e:
			print (e)
	tweets_df["created_at"] = pd.to_datetime(tweets_df["created_at"]) # 作成日のデータをdatetime型に変換
	return tweets_df

def get_profile(user_id):
	user = api.get_user(screen_name = user_id) # ユーザーIDを指定して、ユーザーの情報を取得
	# idはユーザーにランダムに当てはめられた数字、user_idは指定したユーザーID、imageはユーザープロフィールの写真画像URL、descriptionはプロフィールの内容を取得。これらを辞書型で取得して、profileデータを返す
	profile = {
	"id": user.id,
	"user_id": user_id,
	"image": user.profile_image_url,
	"description": user.description # 自己紹介文の取得
	}
	return profile

# Pandasでは、groupby関数を利用して、引数に列を指定してあげると、グループ集計することができる。日付で集計し、それらの値をsum関数で合計し、sort_values関数でcreated_at中にならべる。ascending=Falseは降順
def get_grouped_df(tweets_df):
	grouped_df = tweets_df.groupby(tweets_df.created_at.dt.date).sum().sort_values(by="created_at", ascending=False)
	return grouped_df

# tweets_dfをretweets順に並び替えて、降順にしたものを返す簡単な関数
def get_sorted_df(tweets_df):
	sorted_df = tweets_df.sort_values(by="retweets", ascending=False)
	return sorted_df

# 起動する処理
if __name__ == '__main__':
	app.run(host="localhost")