# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
import streamlit as st
import numpy as np

st.set_page_config(page_title='Cer-T', layout='centered')
st.title("Cer-T  风险预测")
st.write("***")

st.markdown(
    """
<style>
button {
    height: auto;
    padding-top: 15px !important;
    padding-bottom: 15px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.info("注意数据格式：\n\n"
        "1：每行表示1个样本，每列表示样本信息，列可以包括条形码、年龄、性别等信息，但注意列必须提供神经酰胺分子\n\n"
        "2：神经酰胺分子命名必须是大写字母C加上数字，比如C1，C2，C3，C4\n\n"
        "3：输入文件必须含有C1，C2，C3，C4这4列，这4列不能有缺失值和任何中文字符\n\n"
        "4：文件空白处不要加任何注释信息，请严格按照示例准备数据\n\n"
        "5: 示例数据中第一列(无列名字)为程序自动添加，上传的文件不要添加这一列")
st.write("示例：")
example_df = pd.DataFrame()
example_df['条形码'] = range(0, 14)
example_df['性别'] = ["男", "女", "女", "女", "女", "女", "女", "女", "女", "女", "男", "女", "男", "男"]
example_df['年龄'] = [31, 24, 23, 36, 31, 32, 35, 25, 35, 23, 29, 29, 52, 32]
example_df['C1'] = [0.209, 0.198, 0.204, 0.196, 0.180, 0.183, 0.186, 0.199, 0.258, 0.256, 0.344, 0.190, 0.233, 0.171]
example_df['C2'] = [0.054, 0.056, 0.092, 0.060, 0.036, 0.024, 0.037, 0.062, 0.052, 0.078, 0.119, 0.079, 0.063, 0.058]
example_df['C3'] = [2.334, 2.344, 2.589, 2.524, 3.774, 1.353, 2.328, 2.276, 3.739, 2.646, 3.402, 2.148, 3.136, 1.689]
example_df['C4'] = [0.606, 0.738, 0.794, 0.630, 0.440, 0.329, 0.480, 0.587, 0.493, 0.738, 1.015, 0.469, 0.842, 1.526]
st.dataframe(example_df)

@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('gbk')

example_df_csv = convert_df(example_df)

st.download_button(
    label=":red[下载示例数据]",
    data=example_df_csv,
    file_name='示例数据_Cer_T.csv',
    mime='csv',
)

st.write("第一步：选择上传文件（后缀必须是xlsx，csv，xls）")
uploaded_file = st.file_uploader("")
if uploaded_file is not None:
    # st.write(uploaded_file.name)
    suffix_file = os.path.splitext(uploaded_file.name)[1]
    if ('xlsx' in suffix_file) | ('xls' in suffix_file):
        df = pd.read_excel(uploaded_file, index_col=None, header=0)
    elif 'csv' in suffix_file:
        df = pd.read_csv(uploaded_file, index_col=None, header=0, sep=",")
    else:
        st.write("上传文件后缀不符合要求，请重新上传")
else:
    df = None

ref_risk_score = {
    "C1": [0.07, 0.171, 0.21, 0.258, 0.66],
    "C2": [0.01, 0.037, 0.052, 0.07, 0.236],
    "C4": [0.105, 0.46, 0.593, 0.778, 2.201],
    "C1/C3": [0.041, 0.079, 0.095, 0.116, 0.669],
    "C2/C3": [0.005, 0.018, 0.024, 0.032, 0.181],
    "C4/C3": [0.066, 0.211, 0.266, 0.353, 3.847],
}
ref_risk_score = pd.DataFrame(ref_risk_score, index=["0%", "25%", "50%", "75%", "100%"]).T


def mayo_qlife_risk_score(new_df):
    qscore_ranges = {
        0: [10],
        1: list(range(11, 14)),
        2: list(range(14, 18)),
        3: list(range(18, 26)),
        4: list(range(26, 35)),
        5: list(range(35, 43)),
        6: list(range(43, 52)),
        7: list(range(52, 60)),
        8: list(range(60, 69)),
        9: list(range(69, 77)),
        10: list(range(77, 85)),
        11: list(range(85, 93)),
        12: list(range(93, 97)),
    }
    ceramides = ["C1", "C2", "C4", "C1/C3", "C2/C3", "C4/C3"]
    mayo_cal_cols = ['C1_score', 'C2_score', 'C4_score', 'C1/C3_score', 'C2/C3_score', 'C4/C3_score']

    cal_df = pd.DataFrame(index=new_df.index)
    for patient_id in new_df.index:
        per_score = []
        for ceramide in ceramides:
            ceramide_value = new_df.loc[patient_id, ceramide]
            per_score.append(ceramide_value / ref_risk_score.loc[ceramide, "100%"])
            if ceramide_value >= ref_risk_score.loc[ceramide, "75%"]:
                cal_df.loc[patient_id, f"{ceramide}_score"] = 2
            elif ceramide_value < ref_risk_score.loc[ceramide, "50%"]:
                cal_df.loc[patient_id, f"{ceramide}_score"] = 0
            else:
                cal_df.loc[patient_id, f"{ceramide}_score"] = 1

        mean_per_score = np.mean(per_score)
        if mean_per_score >= 1.0:
            mean_per_score = 0.99
        cal_df.loc[patient_id, 'per_score'] = mean_per_score
        cal_df.loc[patient_id, 'Mayo_score'] = cal_df.loc[patient_id, mayo_cal_cols].sum()
        qscore_range = qscore_ranges[cal_df.loc[patient_id, 'Mayo_score']]
        qscore = np.round(np.quantile(qscore_range, q=0.1), 0)
        cal_df.loc[patient_id, '风险得分'] = qscore

        if qscore <= 17.0:
            cal_df.loc[patient_id, '风险等级'] = "低度风险"
        elif (qscore >= 18.0) & (qscore <= 51.0):
            cal_df.loc[patient_id, '风险等级'] = "轻度风险"
        elif (qscore >= 52.0) & (qscore <= 76.0):
            cal_df.loc[patient_id, '风险等级'] = "中度风险"
        elif qscore >= 77.0:
            cal_df.loc[patient_id, '风险等级'] = "高度风险"
    return cal_df



if df is not None:
    st.write("上传数据展示：")
    st.dataframe(df)
    ceramide_match = list(df.columns.intersection(["C1", "C2", "C3", "C4"]))
    if len(ceramide_match) != 4:
        st.error("输入文件必须含有C1，C2，C3，C4这4列，这4列不能有缺失值和任何中文字符")

    if st.button(':red[Run]'):
        new_df = df.copy(deep=True)
        new_df['C1/C3'] = df['C1'] / df['C3']
        new_df['C2/C3'] = df['C2'] / df['C3']
        new_df['C4/C3'] = df['C4'] / df['C3']
        cal_df = mayo_qlife_risk_score(new_df)
        new_df[['风险得分', '风险等级']] = cal_df.loc[new_df.index, ['风险得分', '风险等级']]
        st.success("预测风险结果展示：")
        st.dataframe(new_df)
        new_df_csv = convert_df(new_df)

        st.download_button(
            label="下载预测风险结果",
            data=new_df_csv,
            file_name='预测风险结果_Cer_T.csv',
            mime='csv',
        )


