import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
import os

def get_db_path():
    db_path = "../database/stock_insights.db"
    if not os.path.exists(db_path) and os.path.exists("/tmp/stock_insights.db"):
        db_path = "/tmp/stock_insights.db"
    return db_path

def generate_stock_report(stock_code, time_period):
    start_date, end_date = time_period
    today = datetime.now().date()
    db_path = get_db_path()
    
    report = {
        "stock_code": stock_code,
        "report_period": f"{start_date} to {end_date}"
    }

    with sqlite3.connect(db_path) as conn:
        # Tạo bảng tạm relevant_articles
        conn.execute("DROP TABLE IF EXISTS relevant_articles;")
        conn.execute("""
            CREATE TEMP TABLE relevant_articles AS
            SELECT DISTINCT article_id FROM entities 
            WHERE entity_text =? 
              AND entity_type IN ('STOCK', 'COMPANY')
              AND confidence = 'high'
              AND article_id IN (
                  SELECT article_id FROM articles WHERE publish_date BETWEEN ? AND ?
              );
        """, (stock_code, start_date, end_date))

        # 1. OVERALL SENTIMENT
        q_sentences = """
            SELECT s.sentiment_score, s.sentiment_label, a.publish_date
            FROM sentences s
            JOIN articles a ON s.article_id = a.article_id
            WHERE s.article_id IN (
                SELECT s2.sentence_id FROM sentences s2
                WHERE s2.article_id IN (SELECT article_id FROM relevant_articles)
            )
            AND s.sentiment_score IS NOT NULL;
        """
        df_sent = pd.read_sql_query(q_sentences, conn)
        
        if not df_sent.empty:
            df_sent['publish_date'] = pd.to_datetime(df_sent['publish_date']).dt.date
            df_sent['days_ago'] = (today - df_sent['publish_date']).apply(lambda x: x.days)
            df_sent['weight'] = 1 / (df_sent['days_ago'] + 1)
            weighted_score = (df_sent['sentiment_score'] * df_sent['weight']).sum() / df_sent['weight'].sum()
            # Chuẩn hóa nhãn sentiment về lower-case
            df_sent['sentiment_label'] = df_sent['sentiment_label'].str.lower()
            sentiment_counts = df_sent['sentiment_label'].value_counts().to_dict()
            trend = "Tích cực" if weighted_score > 0.1 else "Tiêu cực" if weighted_score < -0.1 else "Trung tính"
        else:
            weighted_score, sentiment_counts, trend = 0.0, {}, "Không có dữ liệu"

        report["overall_sentiment"] = {
            "score": weighted_score,
            "trend": trend,
            "positive_mentions": sentiment_counts.get("positive", 0),
            "negative_mentions": sentiment_counts.get("negative", 0),
            "neutral_mentions": sentiment_counts.get("neutral", 0)
        }

        # 2. KEY EVENTS, RISKS, PRICE ACTIONS
        def get_key_entities(entity_type):
            query = f"""
                SELECT
                    e.entity_text,
                    COUNT(e.entity_id) as count,
                    AVG(s.sentiment_score) as avg_sentiment
                FROM entities e
                JOIN sentences s ON e.sentence_id = s.sentence_id
                WHERE e.article_id IN (SELECT article_id FROM relevant_articles)
                  AND e.entity_type =?
                GROUP BY e.entity_text
                ORDER BY count DESC
                LIMIT 5;
            """
            df = pd.read_sql_query(query, conn, params=(entity_type,))
            def score_to_label(score):
                if score is None: return "N/A"
                return "Tích cực" if score > 0.1 else "Tiêu cực" if score < -0.1 else "Trung tính"
            df['sentiment'] = df['avg_sentiment'].apply(score_to_label)
            return df.to_dict('records')

        report["key_events"] = get_key_entities('EVENT')
        report["key_price_actions"] = get_key_entities('PRICE_ACTION')
        report["key_risks_mentioned"] = get_key_entities('RISK')

        # 3. TOP RELATED ENTITIES
        q_related = """
            SELECT e.entity_type, e.entity_text
            FROM entities e
            WHERE e.article_id IN (SELECT article_id FROM relevant_articles)
              AND e.entity_text!=?
              AND e.entity_type IN ('STOCK', 'COMPANY', 'PERSON');
        """
        df_related = pd.read_sql_query(q_related, conn, params=(stock_code,))
        top_related = {}
        if not df_related.empty:
            for etype in ['STOCK', 'COMPANY', 'PERSON']:
                top_related[etype.lower() + 's'] = df_related[df_related['entity_type'] == etype]['entity_text'].value_counts().head(3).index.tolist()
        report["top_related_entities"] = top_related

        # 4. SOURCE ARTICLES
        q_articles = """
            SELECT a.title, a.source_url, s.sentiment_label
            FROM articles a
            JOIN sentences s ON a.article_id = s.article_id
            WHERE a.article_id IN (SELECT article_id FROM relevant_articles)
            GROUP BY a.article_id
            ORDER BY a.publish_date DESC
            LIMIT 5;
        """
        df_articles = pd.read_sql_query(q_articles, conn)
        report["source_articles"] = df_articles.to_dict('records')

    return report

# --- HIỂN THỊ BÁO CÁO ---
def show_report(report_data, summary, stock_code_input):
    st.markdown(
        f"<h3 style='text-align: center; color: #30cfd0; margin-top:2rem;'>Báo cáo Phân tích cho {report_data.get('stock_code', stock_code_input)}</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align: center; color: #94a3b8;'>Giai đoạn: {report_data.get('report_period', 'N/A')}</p>", unsafe_allow_html=True)

    st.markdown("#### 🤖 Tóm tắt từ AI")
    st.info(summary)

    # Tổng quan cảm xúc
    st.markdown("#### 📊 Tổng quan Cảm xúc")
    sentiment = report_data['overall_sentiment']
    score = sentiment['score']
    trend_color = "normal"
    if sentiment['trend'] == "Tích cực":
        trend_color = "normal"
        if sentiment['trend'] == "Tiêu cực":
            trend_color = "inverse"

    st.metric(
        label="Điểm Cảm xúc (có trọng số thời gian)",
        value=f"{score:.2f}" if score is not None else "N/A",
        delta=sentiment['trend'],
        delta_color=trend_color
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("👍 Tích cực", sentiment['positive_mentions'])
    col2.metric("👎 Tiêu cực", sentiment['negative_mentions'])
    col3.metric("😐 Trung tính", sentiment['neutral_mentions'])

    # Các bảng chi tiết
    st.markdown("---")

    col_events, col_risks = st.columns(2)
    with col_events:
        st.markdown("#### ⚡ Sự kiện Nổi bật")
        if report_data["key_events"]:
            # Kiểm tra key thực tế
            df_events = pd.DataFrame(report_data["key_events"])
            if 'avg_sentiment' in df_events.columns:
                df_events = df_events.rename(
                    columns={'entity_text': 'Sự kiện', 'avg_sentiment': 'Sentiment'})
                show_cols = ['Sự kiện', 'count', 'Sentiment']
            elif 'sentiment' in df_events.columns:
                df_events = df_events.rename(
                    columns={'entity_text': 'Sự kiện'})
                show_cols = ['Sự kiện', 'count', 'sentiment']
            else:
                df_events = df_events.rename(
                    columns={'entity_text': 'Sự kiện'})
                show_cols = ['Sự kiện', 'count']
            st.dataframe(df_events[show_cols], use_container_width=True)
        else:
            st.write("Không có sự kiện nổi bật.")

    with col_risks:
        st.markdown("#### ⚠️ Rủi ro được đề cập")
        if report_data["key_risks_mentioned"]:
            df_risks = pd.DataFrame(report_data["key_risks_mentioned"])
            if 'avg_sentiment' in df_risks.columns:
                df_risks = df_risks.rename(
                    columns={'entity_text': 'Rủi ro', 'avg_sentiment': 'Sentiment'})
                show_cols = ['Rủi ro', 'count', 'Sentiment']
            elif 'sentiment' in df_risks.columns:
                df_risks = df_risks.rename(
                    columns={'entity_text': 'Rủi ro'})
                show_cols = ['Rủi ro', 'count', 'sentiment']
            else:
                df_risks = df_risks.rename(
                    columns={'entity_text': 'Rủi ro'})
                show_cols = ['Rủi ro', 'count']
            st.dataframe(df_risks[show_cols], use_container_width=True)
        else:
            st.write("Không có rủi ro nổi bật.")

    st.markdown("#### 📈 Hành động Giá Chính")
    if report_data["key_price_actions"]:
        df_price = pd.DataFrame(report_data["key_price_actions"])
        if 'avg_sentiment' in df_price.columns:
            df_price = df_price.rename(
                columns={'entity_text': 'Hành động giá', 'avg_sentiment': 'Sentiment'})
            show_cols = ['Hành động giá', 'count', 'Sentiment']
        elif 'sentiment' in df_price.columns:
            df_price = df_price.rename(
                columns={'entity_text': 'Hành động giá'})
            show_cols = ['Hành động giá', 'count', 'sentiment']
        else:
            df_price = df_price.rename(
                columns={'entity_text': 'Hành động giá'})
            show_cols = ['Hành động giá', 'count']
        st.dataframe(df_price[show_cols], use_container_width=True)
    else:
        st.write("Không có hành động giá nổi bật.")

    # Thực thể liên quan
    st.markdown("---")
    st.markdown("#### 🔗 Các Thực thể Liên quan nhiều nhất")
    related = report_data['top_related_entities']
    if any(related.values()):
        for etype, entities in related.items():
            if entities:
                st.markdown(
                    f"**{etype.replace('_', ' ').title()}:** {', '.join(entities)}")
    else:
        st.write("Không tìm thấy thực thể liên quan nổi bật.")

    # Nguồn bài viết
    st.markdown("---")
    st.markdown("#### 📰 Nguồn Bài viết Tham khảo")
    if report_data["source_articles"]:
        for article in report_data["source_articles"]:
            st.markdown(
                f"- [{article['title']}]({article['source_url']}) - *Cảm xúc: {article['sentiment_label']}*")
    else:
        st.write("Không có bài viết nào trong khoảng thời gian này.")

    st.markdown("</div>", unsafe_allow_html=True)