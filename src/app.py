import numpy as np
import pandas as pd
import sys
import yaml
from ortools.sat.python import cp_model

def __load_products(products_filename: str, shelters_filename:str, volume_factor:int):
    '''
    Load products table, convert volume to int, sort by product type.
    Load shelters and get dict of restrictions.
    '''
    products = pd.read_csv(f'./data/{products_filename}', encoding='utf8')
    # The product price is of floating point type. 
    # For convenience, let's convert to integers. By multiplying by 10
    products['product_volume'] = products['product_volume']*volume_factor
    products['product_volume'] = products['product_volume'].astype(int)
    products.sort_values(['product_type', 'article'], inplace=True)
    products.reset_index(drop=True, inplace=True)

    shelters = pd.read_csv(f'./data/{shelters_filename}', encoding='utf8')
    shelters['product_food'] = shelters['product_food'].apply(lambda x: [int(z) for z in x.split('-')])
    shelters['product_medicines'] = shelters['product_medicines'].apply(lambda x: [int(z) for z in x.split('-')])
    shelters['product_supplies'] = shelters['product_supplies'].apply(lambda x: [int(z) for z in x.split('-')])
    shelters.set_index('shelter_name', inplace=True)
    shelters = shelters.T.to_dict()
    return products, shelters

def __product_type_restrictions(model: cp_model.CpModel, products: pd.DataFrame, bools: list, shelter: dict):
    '''Adding quantity restrictions for a product type'''
    # Makes a table where for each product there is a starting and ending index
    prods_type_start = products.drop_duplicates(subset='product_type', keep='first')['product_type']
    prods_type_start = prods_type_start.reset_index()
    prods_type_start.rename({'index':'start'}, axis=1, inplace=True)
    prods_type_end = products.drop_duplicates(subset='product_type', keep='last')['product_type']
    prods_type_end = prods_type_end.reset_index()
    prods_type_end.rename({'index':'end'}, axis=1, inplace=True)
    prods_type = prods_type_start.merge(prods_type_end, on='product_type')[['product_type', 'start', 'end']]

    # For each type of product we add a restriction specified in the shelter parameters
    for row in prods_type.values:
        if len(shelter[row[0]]) > 1:
            # Restriction from -> to
            model.Add(sum(bools[row[1]:row[2]]) >= shelter[row[0]][0])
            model.Add(sum(bools[row[1]:row[2]]) <= shelter[row[0]][1])
        else:
            # Restriction = x
            model.Add(sum(bools[row[1]:row[2]]) == shelter[row[0]][0])
    return model

def __solution_prepare(solver: cp_model.CpSolver, products: pd.DataFrame, p: np.array, vars_p: list, shelter_name: dict, config: dict):
    '''Preparing DataFrame for output and print parameters'''
    idx = []
    for i in range(len(p)):
        if solver.Value(vars_p[i]) > 0:
                idx.append(i)

    prods = products[products.index.isin(idx)].copy()
    prods['shelter'] = shelter_name

    sum_p = prods['convenience_value'].sum()
    sum_v = prods['product_volume'].sum() / config['volume_factor']
    sum_w = prods['product_price'].sum()
    to_print = f'Find solution for {shelter_name} with params:'
    to_print += f'\nsum of convenience_value = {sum_p}'
    to_print += f'\nsum of product_volume = {sum_v}'
    to_print += f'\nsum of product_price = {sum_w}\n'

    for product_type in prods['product_type'].unique():
        to_print += f"num of {product_type} = {prods[prods['product_type']==product_type].shape[0]}\n"
    print(to_print)

    return prods

def __linear_solver(products: pd.DataFrame, shelters: dict, shelter_name: str, config: dict):
    '''Сreates a model.
    Creates a system of equations and constraints.
    Solves a system of equations
    '''
    model = cp_model.CpModel()

    # Main massive of variables
    p = products['convenience_value'].values
    v = products['product_volume'].values
    w = products['product_price'].values
    vars_p, vars_v, vars_w = [], [], []
    for i in p:
        vars_p.append(model.NewIntVar(0, i, 'p_num'))
    for i in v:
        vars_v.append(model.NewIntVar(0, i, 'v_num'))
    for i in w:
        vars_w.append(model.NewIntVar(0, i, 'w_num'))

    # Maximize function and main restrictions
    model.Maximize(sum(vars_p))
    model.Add(sum(vars_v) >= config['volume_min']*config['volume_factor'])
    model.Add(sum(vars_v) <= config['volume_max']*config['volume_factor'])
    model.Add(sum(vars_w) == config['price_meet'])
    
    # Boolean variables that shows whether the product is selected
    bools = []
    for i in range(len(p)):
        bools.append(model.NewBoolVar(f'b_{i}'))

    # Connection with boolean variables
    for i in range(len(p)):
        model.Add(vars_p[i] > 0).OnlyEnforceIf(bools[i])
        model.Add(vars_p[i] < 1).OnlyEnforceIf(bools[i].Not())

    for i in range(len(p)):
        model.Add(vars_v[i] == v[i]).OnlyEnforceIf(bools[i])
        model.Add(vars_v[i] == 0).OnlyEnforceIf(bools[i].Not())   

    for i in range(len(p)):
        model.Add(vars_w[i] == w[i]).OnlyEnforceIf(bools[i])
        model.Add(vars_w[i] == 0).OnlyEnforceIf(bools[i].Not())
    
    model = __product_type_restrictions(model, products, bools, shelters[shelter_name])

    # Solving
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == 4: #Success
        return __solution_prepare(solver, products, p, vars_p, shelter_name, config)
    else:
        print(f"Can't find solution for {shelter_name}")
        return pd.DataFrame()

def solve(products_filename: str, shelters_filename:str):
    '''
    Main function.
    Data loading and preprocessing.
    Calculation in a cycle for each shelter.
    Saving the result.
    '''
    with open('config.yaml', 'r', encoding='utf8') as c:
        config = yaml.safe_load(c)

    products, shelters = __load_products(products_filename, shelters_filename, config['volume_factor'])

    output = None
    # For each shelter
    for shelter_name in shelters.keys():
        solution = __linear_solver(products, shelters, shelter_name, config)
        if solution.shape[0]>0:
            if output is None:
                output = solution
            else:
                output = pd.concat([output, solution], axis=0, ignore_index=True)
    if output.shape[0] > 0:
        output.to_csv('./data/output.csv', index=False, encoding='utf8')

if __name__ == "__main__":
    products_filename = sys.argv[1]
    shelters_filename = sys.argv[2]
    solve(products_filename, shelters_filename)