import requests  # type: ignore
import json

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

#obtem a lista de compras associada ao utilizador 
def obterListaCompras(api_key, username, hash_user):
    url = f"https://api.spoonacular.com/mealplanner/{username}/shopping-list" 
    params = {
        "apiKey": api_key,
        "hash": hash_user
    } 
    response = requests.get(url, params = params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter a lista de compras: {response.status_code}, {response.text}")
        return None
 
def main():
    #escolha de dieta
    print("Bem vindo ao Planeador de Refeições Inteligentes")
    print("\nOpções de dieta disponíveis: ")
    print("- vegetarian\n- vegan\n- gluten free\n- ketogenic\n- pescetarian\n- paleo\n- etc...\n")
    dieta = input("Qual o tipo de dieta que deseja seguir: ").strip().lower()
    if dieta == "":
        dieta = None
    #ingredientes disponiveis
    ingredientes = [i.strip() for i in input("Que ingredientes tens disponiveis no momento(separados por virgulas): ").strip().split(",")]
    #intolerencias alimentares 
    intolerancias_input = input("Que as intolerâncias alimentares tens(separar por virgulas): ").strip().lower()
    intolerencias = [i.strip() for i in intolerancias_input.split(",")] if intolerancias_input else None
  

    api_key = "5c6f3108b2c34e5d9eb78b8b82a1e4e6"
    #pergunta se deseja gerar plano de refeições
    gerar_plano = input("\nDeseja que lhe seja fornecido um plano de refeições?(sim/nao): ").strip().lower()
    if gerar_plano == "sim":
        time_frame = input("Qual o período do plano?(dia/semana): ").strip().lower()   
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
            meals = plano.get('meals', [])
            if meals:
                print("\nO teu plano de refeições já está disponível. Aqui estão as refeições:")
                for i, refeicao in enumerate(meals, 1):
                    print(f"{i}.{refeicao['title']} (Doses: {refeicao['servings']}, Tempo de preparo: {refeicao['readyInMinutes']} minutos)")
            else:
                print("Não há refeições disponiveis no plano.")
        else:
            print("Não foi possível criar o teu plano de refeições.")
    else:
        #pesquisa de receitas com base nos ingredientes fornecidos
        print("\nApresentar receitas com ingredientes disponiveis.")
        receitas = obterReceitas(ingredientes, api_key, dieta=dieta, intolerancias=intolerencias)
        
        #lista todas as receitas que forem encontradas
        if receitas:
            print(f"\nReceitas disponiveis {len(receitas)} com os ingredientes fornecidos:\n")
            for i, receita in enumerate(receitas, 1):
                print(f"{i}.{receita['title']}")

        escolha = input("\nEscolha o número da receita que deseja observar detalhadamente: ")
        try:
            receita_escolhida = receitas[int(escolha) - 1]
        except (IndexError, ValueError):
            print("Escolha inválida.")
            return
            
        detalhes = obterDetalhesReceita(receita_escolhida['id'], api_key)
        if detalhes:
            calorias, proteinas, gorduras, hidratos = valoresNutricionais(detalhes.get('nutrition', {}))
            sabor = detalhes.get('taste', {})
            ingredientes_usados = [ingrediente['name'] for ingrediente in detalhes.get('extendedIngredients', [])]

            print(f"\n{detalhes['title']}")
            print(f"Tempo de preparo: {detalhes.get('readyInMinutes', 'N/A')} min")
            print(f"Número doses: {detalhes.get('servings', 'N/A')}")
            print(f"\nIngredientes necessarios para {detalhes['title']}: ")
            for ing in ingredientes_usados:
                print(f" - {ing}")

            print(f"Valores Nutricionais: {calorias} kcal | {proteinas} proteina | {gorduras} gordura | {hidratos} hidratos")

            likes = detalhes.get('aggregateLikes', 'N/A')
            pontuacao = detalhes.get('spoonacularScore', 'N/A')

            print(f"\nAvaliações da receita:")
            print(f" - Likes: {likes}")
            print(f" - Pontuação Spoonacular: {pontuacao}/100")

            if pontuacao != 'N/A':
                if pontuacao >= 80:
                    print("Receita muito bem avaliada pelos nossos utilizadores.")
                elif pontuacao >= 50 and pontuacao < 80:
                    print("Receita com uma avaliacão razoavel.")
                else:
                    print("Receita pouco recomendada pelos nossos utilizadores.")

            modo_preparo = obterModoPreparo(receita_escolhida['id'], api_key)
            if modo_preparo:
                print("\nModo de preparo:")
                for instrucao in modo_preparo:
                    for passo in instrucao.get('steps', []):
                        print(f"Passo {passo['number']}: {passo['step']}")
            else:
                print("\nModo de preparo não disponivel.")
            if sabor:
                print("\nPerfil de sabor:")
                for key, value in sabor.items():
                    print(f" {key.capitalize()}: {round(value, 2)}")
            mostrarComentarios(receita_escolhida['id'])
            adicionar_comentario = input("\nDeseja adicionar um comentario sobre esta receita?(sim/nao):").strip().lower()
            if adicionar_comentario == "sim":
                nome_utilizador = input("Insira o seu nome de utilizador: ").strip()
                comentario = input("Escreva o seu comentario: ").strip()
                guardarComentario(receita_escolhida['id'], comentario, nome_utilizador)
                print("Comentario guardado com sucesso.")
            
            print("=" * 70)
            print("\n")

            substituir = input("\nDeseja receber sugestões de substitutos para algum ingrediente desta receita?(sim/nao): ").lower()
            if substituir == "sim":
                ingrediente_subtituir = input("Qual o nome do ingrediente que deseja procurar por substitutos:  ").strip()
                substitutos = substituicaoIngrediente(ingrediente_subtituir, api_key)
                if substitutos:
                    print(f"\nSubstitutos para {ingrediente_subtituir}:")
                    for sub in substitutos:
                        print(f" - {sub}")  
                else:
                    print(f"\nInfelizmente, não foi possivel encontrar substitutos para {ingrediente_subtituir}.")       
        else:
            print("Não foram encontradas receitas com os ingredientes fornecidos.")
        
        ver_lista = input("\nDeseja observar a sua lista de compras?(sim/nao): ").strip().lower()
        if ver_lista == "sim":
            username = input("Insira o seu username: ").strip()
            hash_user = input("Insira o seu hash de usuario: ").strip()

            lista_compras = obterListaCompras(api_key, username, hash_user)

            if lista_compras and 'aisles' in lista_compras:
                print("\nAqui está a sua lista de compras organizada:\n")
                for seccao in lista_compras['aisles']:
                    print(f"Secção: {seccao['aisle']}")
                    for item in seccao['items']:
                        nome = item['name']
                        quantidade = item['measures']['metric']['amount']
                        unidade = item['measures']['metric']['unit']
                        print(f" - {nome}: {quantidade} {unidade}")
                print(f"Total estimado: {round(lista_compras.get('cost', 0), 2)}€")
            else:
                print("Não foi possivel obter a lista de compras.")
#execucao do programa principal
if __name__ == "__main__":
    main()

