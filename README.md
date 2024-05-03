# Multi dimension knapsack problem with linear solver.

## Annotation.
In different companies where I worked, I was faced with the knapsack problem with different restrictions. There is no mystery in the problem itself and it is well known as the methods for solving it.  
But every time I couldn’t find a good template that I could quickly adapt to my needs. So I’ll try to provide here a good and clear example that could be reused with minor changes for different tasks.  
The solution to the problem itself can be divided into 3 stages:
- reading and pre-processing of data
- drawing up a system of linear equations with restrictions
- solving equations using Google [OR-Tools](https://developers.google.com/optimization/cp/cp_solver) with [python cp model](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)

## Formulation of the problem.
Let's imagine that you and I work in a fund to support animal shelters. We work with suppliers of pet products. Our task is to deliver goods to different shelters, taking into account the needs of the shelters themselves, the cost of goods and their convenience. Accordingly we have two tables, one with all products and the second with shelters and their needs.

### Products table
> article - just vendor number, unique.

> convenience_value - Conditional scoring of the product, in the range of 0-100. The higher the value of a product, the more accessible, better priced and faster it ships. **What we will maximize.**

> product_volume - Each product occupies some place. Transportation of products is carried out using a car. That's why we don't want to drive a half-empty car. **Therefore, it should be filled with 7-9 cubic meters**.

> product_type - Three types of product available: food, medicines, and supplies.

> product_price - The price is indicated in credits. **For each delivery we must meet 1000 credits.**

### Shelters table
> shelter_name - just a name

> product_food - The required quantity of goods of the corresponding type. Can be specified rigidly or in an interval. For example (5), (0-3).

> product_medicines - The required quantity of goods of the corresponding type. Can be specified rigidly or in an interval.

> product_supplies - The required quantity of goods of the corresponding type. Can be specified rigidly or in an interval.

## Solving the problem.
To solve the problem, we need to create a system of linear equations:  
1. $ \sum_{i=1}^n p_i b_i  => max$  
where $p$ - convenience_value  
and $b$ - int variable that takes a value from 0 to 1. Essentially showing whether to take a certain product or not

2. $ \sum_{i=1}^n v_i b_i \geq 7$ and $ \sum_{i=1}^n v_i b_i \leq 9$  
where $v$ - product_volume

3. $ \sum_{i=1}^n \omega_i b_i = 1000$  
where $\omega$ - product_price

4. $ \sum_{i=1}^n f_i b_i \geq k$ and $ \sum_{i=1}^n f_i b_i \leq j$  
where $f$ - food products, and $k$, $j$ - The required quantity interval

5. $ \sum_{i=1}^n m_i b_i \geq k$ and $ \sum_{i=1}^n m_i b_i \leq j$  
where $m$ - medicine products

6. $ \sum_{i=1}^n \theta_i b_i \geq k$ and $ \sum_{i=1}^n \theta_i b_i \leq j$  
where $\theta$ - supplies products

## Run script
To run the script in the terminal, you need to pass command line arguments in the form of the names of files with products and shelters.  
`python ./src/app.py products.csv shelters.csv`  
If the script is successfully executed, you should see this output in the terminal:
```
Find solution for shelter_1 with params:
sum of convenience_value = 1030
sum of product_volume = 9.0
sum of product_price = 1000
num of product_food = 1
num of product_medicines = 4
num of product_supplies = 6

Find solution for shelter_2 with params:
sum of convenience_value = 1163
sum of product_volume = 9.0
sum of product_price = 1000
num of product_food = 3
num of product_medicines = 4
num of product_supplies = 6

Find solution for shelter_3 with params:
sum of convenience_value = 879
sum of product_volume = 9.0
sum of product_price = 1000
num of product_food = 3
num of product_medicines = 3
num of product_supplies = 3

Can't find solution for shelter_4
```