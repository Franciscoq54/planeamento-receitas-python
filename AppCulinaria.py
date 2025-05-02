import requests  # type: ignore
import json
import os
from datetime import datetime

#gera um plano de refeicoes utilizando a API sPOONACULAR
def planoRefeicoes(api_key, time_frame = 'day', target_calories = None, dieta = None, excluir = None):
    url = "https://api.spoonacular.com/mealplanner/generate"
    params = {
        "timeFrame": time_frame,
        "apiKey": api_key
    }
    if target_calories:
        params["targetCalories"] = target_calories
    if dieta:
        params["diet"] = dieta
    if excluir:
        params["exclude"] = excluir
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()                                                      
    else:
        #se a resposta da API nao for 200(ok), imprime o erro e retorna None
        print(f"Erro ao gerar plano de refeições: {response.status_code}, {response.text}")
        return None

#pesquisa receitas baseadas nos ingredientes disponiveis    
def obterReceitas(ingredientes, api_key, numero_receitas = 5, dieta = None, intolerancias = None):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = { 
        "includeIngredients": ",".join(ingredientes) ,
        "number": numero_receitas,
        "ranking": 1, #priorizar receitas que usam mais os ingredientes disponiveis
        "ignorePantry": True, #ignora items tipos  da despensa(sal, agua, etc)
        "apiKey": api_key
    }
    if dieta:
        params["diet"] = dieta
    if intolerancias:
        params['intolerances'] = ",".join(intolerancias)

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', []) 
    else:
        print("Erro ao obter receitas: ", response.status_code, response.text)
        return[]

#obtem informacoes detalhadas acerca de uma receita especifica
def obterDetalhesReceita(receita_id, api_key):
    url = f"https://api.spoonacular.com/recipes/{receita_id}/information"
    params = {
        "includeNutrition":True,
        "addTasteData": True, #adicionado para trazer dados de sabor(agridoce, doce, salcado, etc)
        "apiKey": api_key
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter detalhes da receita {receita_id}: ", response.status_code, response.text)
        return {}

#extrai os valores nutricionais principais(calorias, proteinas, gorduras, hidratos)   
def valoresNutricionais(valNutricionais):
    calorias = proteinas = gorduras = hidratos = "N/A"

    if valNutricionais and 'nutrients' in valNutricionais:
        for item in valNutricionais['nutrients']:
            nome = item['name'].lower()
            if nome == "calories":
                calorias = f"{item['amount']} {item['unit']}"
            elif nome == "protein":
                proteinas = f"{item['amount']} {item['unit']}"
            elif nome == "fat":
                gorduras = f"{item['amount']} {item['unit']}"
            elif nome == "carbohydrates":
                hidratos = f"{item['amount']} {item['unit']}"
    return calorias, proteinas, gorduras, hidratos            

#obtem o passo-a-passo do modo de preparo da receita
def obterModoPreparo(receita_id, api_key):
    url = f"https://api.spoonacular.com/recipes/{receita_id}/analyzedInstructions"
    params = {
        "apiKey":api_key,
        "stepBreakdown": True #divide ainda mais as etapas da receita
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter o modo de preparo da receita {receita_id}: ", response.status_code, response.text)
        return []

#sugere substitutos para um ingrediente 
def substituicaoIngrediente(nome_ingrediente, api_key):
    url = "https://api.spoonacular.com/food/ingredients/substitutes" 
    params = {
        "ingredientName": nome_ingrediente,
        "apiKey": api_key
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        dados = response.json()
        if "substitutes" in dados:
            return dados["substitutes"]
        else:
            print(f"\nNão há substitutos disponiveis para {nome_ingrediente}.")
            return []
    else:
        print(f"Erro ao obter substitutos para {nome_ingrediente}: ", response.status_code, response.text)
        return []

#guarda um comentario feito a uma receita no ficheiro json local
def guardarComentario(receita_id, comentario, nome_utilizador):
    try:
        with open('comentarios.json', 'r', encoding='utf-8') as f:
            comentarios = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        comentarios = {}
    
    if str(receita_id) not in comentarios:
        comentarios[str(receita_id)] = []
    
    comentarios[str(receita_id)].append({
        "utilizador": nome_utilizador,
        "comentario": comentario
    })
    with open('comentarios.json', 'w', encoding = 'utf-8') as f:
        json.dump(comentarios, f, indent=4, ensure_ascii=False)

#exibe todos os comentarios associados a uma receita
def mostrarComentarios(receita_id):
    try:
        with open('comentarios.json', 'r', encoding='utf-8') as f:
            comentarios = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        comentarios = {}    
    if str(receita_id) in comentarios:
        print("\nComentários de utilizadores sobre esta receita:")
        for c in comentarios[str(receita_id)]:
            print(f"- {c['utilizador']}: {c['comentario']}")
    else:
        print("\nAinda não existem comentários para esta receita.")

#obtem lista de compras para o plano gerado
def obterListaCompras(meals, api_key):
    lista_ingredientes = {}
    print("\nA gerar lista de compras de acordo com as receitas fornecidas.")

    for refeicao in meals:
        detalhes = obterDetalhesReceita(refeicao['id'], api_key)
        if detalhes:
            for ingrediente in detalhes.get("extendedIngredients", []):
                nome = ingrediente['name']
                medidas_metric = ingrediente.get('measures', {}).get('metric', {})
                quantidade = medidas_metric.get('amount', 0)

                if nome in lista_ingredientes:
                    lista_ingredientes[nome]['quantidade'] += quantidade
                else:
                    lista_ingredientes[nome] = {
                        'quantidade': quantidade,
                    }
    print("\nLista de compras necessarias para o seu plano:")
    for nome, info in lista_ingredientes.items():
        print(f" - {nome}: {round(info['quantidade'], 2)}")
    
    guardarListaCompras(lista_ingredientes)

def guardarListaCompras(lista_ingredientes):
    with open('lista_compras.txt', 'w', encoding='utf-8') as f:
        f.write("Lista de compras:\n\n")
        for nome, info in lista_ingredientes.items():
            f.write(f"{nome}: {round(info['quantidade'], 2)}\n")
    print("\nA lista de compras foi guardada com sucesso.")

def guardarPlanoHistorico(plano, dieta, calorias):
    try:
        with open('historico.json', 'r', encoding='utf-8') as f:
            historico = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        historico = []
    
    historico.append({
        "data":datetime.now().strftime("%d-%m-%y %H:%M"),
        "dieta": dieta if dieta else "Nenhuma",
        "calorias": calorias if calorias else "Não definido",
        "refeicoes": [ref['title'] for ref in plano.get('meals', [])]
    })

    with open('historico.json', 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)
    print("\nPlano guardado no histórico com sucesso.")

def mostarHistorico():
    try:
        with open('historico.json', 'r', encoding='utf-8') as f:
            historico = json.load(f)
        print("\nHistórico de planos anteriores: ")
        for item in historico:
            print(f"\nData: {item['data']}")
            print(f"Dieta: {item['dieta']}")
            print(f"Calorias: {item['calorias']}")
            print("Refeições: ")
            for ref in item['refeicoes']:
                print(f" - {ref}")
    except FileNotFoundError:
        print("Ainda não existe planos guardados no histórico.")

def main():
    #escolha de dieta
    print("Bem vindo ao Planeador de Refeições:")
    ver_historico = input("Deseja consultar planos anteriores guardados? (sim/nao): ").strip().lower()
    if ver_historico == "sim":
        mostarHistorico()
        
    print("\nOpções de dieta disponíveis: ")
    print("- vegetarian\n- vegan\n- gluten free\n- ketogenic\n- pescetarian\n- paleo\n- etc...\n")
    dieta = input("Qual o tipo de dieta que deseja seguir: ").strip().lower()
    if dieta == "":
        dieta = None
    #ingredientes disponiveis
    ingredientes = [i.strip() for i in input("Que ingredientes tem disponivel no momento(separados por virgulas): ").strip().split(",")]
    #intolerencias alimentares 
    intolerancias_input = input("Tem alguma intolerencia alimentar(separar por virgulas): ").strip().lower()
    intolerencias = [i.strip() for i in intolerancias_input.split(",")] if intolerancias_input else None
  

    api_key = "5c6f3108b2c34e5d9eb78b8b82a1e4e6"
  
   
    print("\nSerá gerado um plano de refeições personalizado de acordo com as suas perferencias:")
    
    while True:
        time_frame = input("Qual o período do plano?(dia/semana): ").strip().lower()   
        if time_frame in ["dia", "semana"]:
             break
        else:
                print("Entrada inválida. Escreva 'dia' ou 'semana'.")

    target_calories_input = input("Qual a meta de calorias para o plano?").strip()
    target_calories = None
    if target_calories_input:
        try:
            target_calories = int(target_calories_input)
        except ValueError:
            print("Valor de calorias inserido é invalido.")
            target_calories = None
    #gera o plano de refeições
    plano = planoRefeicoes(api_key, time_frame=time_frame, target_calories=target_calories, dieta=dieta, excluir=",".join(intolerencias) if intolerencias else None)

    if plano:
        guardarPlanoHistorico(plano, dieta, target_calories)
        meals = plano.get('meals', [])
        if meals:
            print("\nO teu plano de refeições já está disponível. Aqui estão as refeições:")
            for i, refeicao in enumerate(meals, 1):
                print(f"{i}. {refeicao['title']} (Doses: {refeicao['servings']}, Tempo de preparo: {refeicao['readyInMinutes']} minutos)")
            escolha = input("\nIndique o número da receita do plano que deseja consultar detalhadamente:")
            try:
                refeicao_escolhida = meals[int(escolha) - 1]
            except (IndexError, ValueError):
                print("Escolha inválida.")
                return 
            detalhes = obterDetalhesReceita(refeicao_escolhida['id'], api_key)
            if detalhes:
                calorias, proteinas, gorduras, hidratos = valoresNutricionais(detalhes.get('nutrition', {}))
                sabor = detalhes.get('taste', {})
                ingredientes_usados = [ingrediente['name'] for ingrediente in detalhes.get('extendedIngredients', [])]
                    
                print(f"\n{detalhes['title']}")
                print(f"Tempo de preparo: {detalhes.get('readyInMinutes', 'N/A')} min")
                print(f"Número de doses: {detalhes.get('servings', 'N/A')}")
                print(f"\nIngredientes necessários para {detalhes['title']}:")
                for ing in ingredientes_usados:
                    print(f" - {ing}")
                print(f"\nInformação Nutricional: {calorias} Kcal | {proteinas} proteína | {gorduras} gordura | {hidratos} hidratos")

                modo_preparo = obterModoPreparo(refeicao_escolhida['id'], api_key)
                if modo_preparo:
                    print("\nModo de preparação:")
                    for instrucao in modo_preparo:
                        for passo in instrucao.get('steps', []):
                            print(f"Etapa {passo['number']}: {passo['step']}")
                else:
                    print("\nModo de preparo não disponível.")

                if sabor:
                    print("\nPerfil de sabores:")
                    for key, value in sabor.items():
                        print(f" {key.capitalize()}: {round(value, 2)}")
                    
                mostrarComentarios(refeicao_escolhida['id'])
                adicionar_comentario = input("\nPretende adicionar um comentário sobre esta receita?(sim/nao): ").strip().lower()
                if adicionar_comentario == "sim":
                    nome_utilizador = input("Insira o nome de utilizador: ").strip()
                    comentario = input("Escreva o seu comentário: ").strip()
                    guardarComentario(refeicao_escolhida['id'], comentario, nome_utilizador)
                    print("Comentário guardado com sucesso.")
                    
                substituir = input("\nDeseja receber sugestões de substitutos para algum ingrediente desta receita?(sim/nao): ").lower()
                if substituir == "sim":
                    ingrediente_subtituir = input("Qual o ingrediente que deseja procurar por substitutos: ").strip()
                    substitutos = substituicaoIngrediente(ingrediente_subtituir, api_key)
                    if substitutos:
                        print(f"\nSubstitutos para {ingrediente_subtituir}: ")
                        for sub in substitutos:
                            print(f" - {sub}")
                    else:
                        print(f"\nInfelizmente, não foi possível encontrar substitutos para {ingrediente_subtituir}.")
                ver_lista = input(f"\nDeseja consultar a lista de compras que necessita? (sim/nao): ").strip().lower()
                if ver_lista == "sim":
                    obterListaCompras(meals, api_key)    
            else:
                print("Não foi possível obter os detalhes da receita.")
        else:
            print("Não há refeições disponiveis no plano.")
    else:
        print("Não foi possível criar o teu plano de refeições.")
   
#execucao do programa principal
if __name__ == "__main__":

    main()

