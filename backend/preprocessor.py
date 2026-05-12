import re
import pandas as pd

def preprocess(file):
    data=file.read().decode("utf-8")
    pattern=r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'
    date=re.findall(pattern,data)
    date=date[1:]
    message=re.split(pattern,data)[2:]
    df=pd.DataFrame({
    "date":date,
    "message":message
    })
    df["user"]=df["message"].apply(lambda x:x.split(":",1)[0])
    df["text"]=df["message"].apply(lambda x:x.split(":",1)[1])
    df["date"]=pd.to_datetime(df["date"],format= '%d/%m/%Y, %H:%M - ')
    df["year"]=df["date"].dt.year
    df["month"]=df["date"].dt.month_name()
    df["day"]=df["date"].dt.day
    df["minute"]=df["date"].dt.minute
    df["hour"]=df["date"].dt.hour
    return df

def word_count(df, user=None):
    msg_df = df if user is None else df[df["user"] == user]
    msg_df = msg_df[~msg_df["text"].str.contains("Media omitted", na=False)]
    text = msg_df["text"].dropna().str.lower().str.cat(sep=" ")
    words = text.split()
    from collections import Counter
    return dict(Counter(words).most_common(20))

def most_active_time(df,user=None):
    time={}
    msg_df = df if user is None else df[df["user"] == user]
    for col in ["hour", "minute", "year","month", "day"]:
        time[col]=msg_df[col].value_counts().to_dict()
    return time

def message_stats(df,user=None):
    msg_df = df if user is None else df[df["user"] == user]
    msg_df=msg_df[~msg_df["text"].str.contains("Media omitted", na=False)]
    return {
        "total_messages":len(msg_df),
        "avg_msg_length":round(msg_df["text"].str.len().mean(),2),
        "total_characters":int(msg_df["text"].str.len().sum()),
    }

def day_of_week_activity(df,user=None):
    msg_df = df if user is None else df[df["user"] == user]
    return msg_df["date"].dt.day_name().value_counts().to_dict()

def monthly_timeline(df, user=None):
    msg_df = df if user is None else df[df["user"] == user]
    year_month=msg_df["date"].dt.to_period("M").astype(str)
    return year_month.value_counts().sort_index().to_dict()

def emoji_count(df,user=None):
    msg_df = df if user is None else df[df["user"] == user]
    emoji_pattern=re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
        "\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF\U00002600-\U000026FF]",flags=re.UNICODE
    )
    all_emojis=msg_df["text"].dropna().apply(lambda x:emoji_pattern.findall(x))
    flat=[e for sublist in all_emojis for e in sublist]
    from collections import Counter
    return dict(Counter(flat).most_common(20))

def conversation_starter(df,gap_hours=4):
    # who sends the first message after a silence of gap_hours
    df_sorted=df.sort_values("date").reset_index(drop=True)
    time_diff=df_sorted["date"].diff()
    gap=pd.Timedelta(hours=gap_hours)
    starters=df_sorted[time_diff>gap]["user"].value_counts().to_dict()
    return starters

def longest_streak(df):
    # longest streak of consecutive days with at least 1 message
    dates=df["date"].dt.date.unique()
    dates=sorted(dates)
    if len(dates)==0:
        return {"streak_days":0,"start":"","end":""}
    best=1
    current=1
    best_start=dates[0]
    best_end=dates[0]
    curr_start=dates[0]
    for i in range(1,len(dates)):
        if (dates[i]-dates[i-1]).days==1:
            current+=1
        else:
            if current>best:
                best=current
                best_start=curr_start
                best_end=dates[i-1]
            current=1
            curr_start=dates[i]
    if current>best:
        best=current
        best_start=curr_start
        best_end=dates[-1]
    return {"streak_days":best,"start":str(best_start),"end":str(best_end)}

def ghost_detector(df):
    # longest silence (gap) per user in hours
    result={}
    for user in df["user"].unique():
        user_df=df[df["user"]==user].sort_values("date")
        if len(user_df)<2:
            result[user]=0
            continue
        gaps=user_df["date"].diff().dropna()
        mean_gap=gaps.mean()
        result[user]=round(mean_gap.total_seconds()/3600,2)  # in hours
    return result

def night_owl_or_early_bird(df):
    # classify each user based on their peak messaging hour
    result={}
    for user in df["user"].unique():
        user_df=df[df["user"]==user]
        peak_hour=user_df["hour"].value_counts().idxmax()
        if 5<=peak_hour<12:
            label="Early Bird"
        elif 12<=peak_hour<17:
            label="Afternoon Chatter"
        elif 17<=peak_hour<21:
            label="Evening Texter"
        else:
            label="Night Owl"
        result[user]={"peak_hour":int(peak_hour),"label":label}
    return result

def activity_heatmap(df, user=None):
    # hour x day_of_week message counts
    msg_df = df if user is None else df[df["user"] == user]
    df_copy=msg_df.copy()
    if df_copy.empty: return {}
    df_copy["day_name"]=df_copy["date"].dt.day_name()
    heatmap=df_copy.groupby(["day_name","hour"]).size().reset_index(name="count")
    result={}
    for _,row in heatmap.iterrows():
        day=row["day_name"]
        if day not in result:
            result[day]={}
        result[day][int(row["hour"])]=int(row["count"])
    return result


def get_analysis(df):
    count = {}
    count["people"] = {}
    count["media_count"] = {}
    users = df["user"].unique()
    for user in users:
        count["people"][user] = df[df["user"] == user].shape[0]
        count["media_count"][user] = df[(df["user"] == user) & (df["text"].str.contains("Media omitted", na=False))].shape[0]

    #word counts
    count["word_count"] = word_count(df)
    count["per_user_word_count"] = {u: word_count(df, u) for u in users}

    #timed analysis
    count["active_time"]=most_active_time(df)
    count["per_user_active_count"]={u: most_active_time(df,u) for u in users}

    #message stats
    count["message_stats"]=message_stats(df)
    count["per_user_message_stats"]={u: message_stats(df,u) for u in users}

    #day of week
    count["day_of_week"]=day_of_week_activity(df)
    count["per_user_day_of_week"]={u: day_of_week_activity(df,u) for u in users}

    #monthly timeline
    count["monthly_timeline"]=monthly_timeline(df)
    count["per_user_monthly_timeline"]={u: monthly_timeline(df,u) for u in users}

    #emoji counts
    count["emoji_count"]=emoji_count(df)
    count["per_user_emoji_count"]={u: emoji_count(df,u) for u in users}

    #conversation starters
    count["conversation_starters"]=conversation_starter(df)

    #longest streak
    count["longest_streak"]=longest_streak(df)

    #ghost detector (longest silence per user in hours)
    count["ghost_detector"]=ghost_detector(df)

    #night owl vs early bird
    count["night_owl_or_early_bird"]=night_owl_or_early_bird(df)

    #activity heatmap (hour x day_of_week)
    count["activity_heatmap"]=activity_heatmap(df)
    count["per_user_activity_heatmap"]={u: activity_heatmap(df,u) for u in users}

    return count 
