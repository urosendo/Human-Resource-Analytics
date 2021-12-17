#carregando as bibliotecas
import pandas as pd
import streamlit as st
from minio import Minio
import joblib
import matplotlib.pyplot as plt
from pycaret.classification import load_model, predict_model

#Baixando os aquivos do Data Lake
client = Minio(
        "172.17.0.3:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

#modelo de classificacao,dataset e cluster.
client.fget_object("curated","model.pkl","model.pkl")
client.fget_object("curated","dataset.csv","dataset.csv")
client.fget_object("curated","cluster.joblib","cluster.joblib")

var_model = "model"
var_model_cluster = "cluster.joblib"
var_dataset = "dataset.csv"

#carregando o modelo treinado.
model = load_model(var_model)
model_cluster = joblib.load(var_model_cluster)

#carregando o conjunto de dados.
dataset = pd.read_csv(var_dataset)

# título
st.title("Human Resource Analytics")

# subtítulo
st.markdown("Este é um Data App utilizado para exibir a solução de Machine Learning para o problema de Human Resource Analytics.")

# # imprime o conjunto de dados usado
# st.dataframe(dataset.head())

# grupos de empregados.
kmeans_colors = ['green' if c == 0 else 'red' if c == 1 else 'blue' for c in model_cluster.labels_]

#st.sidebar.subheader("Defina os atributos do colaborador para predição")

# mapeando dados do usuário para cada atributo
name = st.sidebar.text_input('Colaborador', 'Ullysses')
satisfaction = st.sidebar.slider("Satisfação", min_value=0, max_value=100, value=int(dataset["satisfaction"].mean()))
evaluation = st.sidebar.slider("Avaliação", min_value=0, max_value=100, value=int(dataset["evaluation"].mean()))
averageMonthlyHours = st.sidebar.number_input("Média de horas mensais", min_value=0.0, value=dataset["averageMonthlyHours"].mean())
yearsAtCompany = st.sidebar.number_input("Anos na empresa", min_value=0.0, value=dataset["yearsAtCompany"].mean())

# inserindo um botão na tela
btn_predict = st.sidebar.button("Realizar Classificação")

# verifica se o botão foi acionado
if btn_predict:
    data_teste = pd.DataFrame()
    data_teste["satisfaction"] = [satisfaction]
    data_teste["evaluation"] =	[evaluation]    
    data_teste["averageMonthlyHours"] = [averageMonthlyHours]
    data_teste["yearsAtCompany"] = [yearsAtCompany]
    
    #realiza a predição
    result = predict_model(model, data=data_teste)

    features_model = ["satisfaction", "evaluation", "averageMonthlyHours", "yearsAtCompany"]
    df_mean = dataset[features_model].mean().reset_index(name='mean')
    df_mean.index = df_mean['index']
    del df_mean['index']
    
    df_result = result[features_model].T
    df_result.columns = ['colaborador']
    df_all = pd.concat([df_mean, df_result], axis=1)
    df_all['diff'] = ((df_all['colaborador']  - df_all['mean'])/df_all['mean']) * 100

    delta_satisfaction = df_all['diff']["satisfaction"]
    delta_evaluation = df_all['diff']["evaluation"]
    delta_averageMonthlyHours = df_all['diff']["averageMonthlyHours"]
    delta_yearsAtCompany = df_all['diff']["yearsAtCompany"]

    mean_satisfaction = df_all['mean']["satisfaction"]
    mean_evaluation = df_all['mean']["evaluation"]
    mean_averageMonthlyHours = df_all['mean']["averageMonthlyHours"]
    mean_yearsAtCompany = df_all['mean']["yearsAtCompany"]
    
    score = result.iloc[0]['Score']
    label = result.iloc[0]['Label']

    if int(label) == 1:
        turnover = 'sair'
    else:
        turnover = 'continuar'

    st.header(f'Informações dos colaboradores da Empresa')

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Satisfação Média", f"{mean_satisfaction:.2f}")
    col2.metric("Avaliação Média", f"{mean_evaluation:.2f}")
    col3.metric("Média de horas mensais", f"{mean_averageMonthlyHours:.2f}")
    col4.metric("Média de Anos na Empresa", f"{mean_yearsAtCompany:.2f}")



    
    st.header(f'Informações do Colaborador {name}')
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Satisfação", f"{satisfaction:.2f}", f"{delta_satisfaction:.2f}%")
    col2.metric("Avaliação", f"{evaluation:.2f}", f"{delta_evaluation:.2f}%")
    col3.metric("Média de horas mensais", f"{averageMonthlyHours:.2f}", f"{delta_averageMonthlyHours:.2f}%")
    col4.metric("Anos na Empresa", f"{yearsAtCompany:.2f}", f"{delta_yearsAtCompany:.2f}%")

    st.subheader(f'A probabilidade do colaborador {name} {turnover} da empresa é de {score:.2f}')
  

    fig = plt.figure(figsize=(10, 3))
    plt.scatter( x="satisfaction"
                ,y="evaluation"
                ,data=dataset[dataset.turnover==1],
                alpha=0.25,color = kmeans_colors)

    plt.xlabel("Satisfação")
    plt.ylabel("Avaliação")

    plt.scatter( x=model_cluster.cluster_centers_[:,0]
                ,y=model_cluster.cluster_centers_[:,1]
                ,color="black"
                ,marker="X",s=100)
    
    plt.scatter( x=[satisfaction]
                ,y=[evaluation]
                ,color="yellow"
                ,marker="X",s=300)

    plt.title("Grupos de Empregados - Satisfação vs Avaliação.")
    plt.show()
    st.pyplot(fig) 

    st.markdown("- **Cluster Verde:** colaboradores bem avaliados e insatisfeitos.")

    st.markdown("- **Cluster Vermelho:** colaboradores mal avaliados e insatisfeitos.") 

    st.markdown("- **Cluster Azul:** colaboradores bem avaliados e satisfeitos.")


    st.markdown('### **Satisfação**')
    st.markdown("- Colaboradores com o nível de satisfação em 20 ou menos tendem a deixar a empresa.")
    st.markdown("- Colaboradores com o nível de satisfação em até 50 tem maior probabilidade de deixar a empresa")

    st.markdown('### **Avaliação**')
    st.markdown("- Colaboradores com **baixa performance** e **alta performance** tendem a deixar a empresa")
    st.markdown("- O **ponto ideal** para os colaboradores que permaneceram está dentro da avaliação de 60 à 80.")

    st.markdown('### **Média de horas mensais**')
    st.markdown("- A concentração da quantidade de horas trabalhadas nos últimos 3 meses está ao redor da média em 275 horas.")

    st.markdown('### **Anos na empresa**')
    st.markdown("- Colaboradores com **4 e 5 anos de casa** deixaram a empresa.")
    st.markdown("- Colaboradores acima de **5 anos de casa** devem ser examinados.")




# ##  Turnover V.S. YearsAtCompany 
# ***
# **Resumo:** Vamos ver mais alguns pontos para entender o porque os empregados deixam a empresa.
#  - Empregados com **4 e 5 anos de casa** deixaram a empresa.
#  - Empregados acima de **5 anos de casa** devem ser examinados.
 
# **Questões:**
#   - Por que os Empregados estão saindo principalmente na faixa de 3-5 anos?
#   - Quem são esses Empregados que saíram?