# -*- coding: utf-8 -*-            
# @Time : 2023/12/30 1:32
# @Author: yxli
# @FileName: unit_function_256.py
# @Software: PyCharm
from constrain_condition import *

# Takes in a list of variables and a list of constraint terms from the constraint_condition file,
# and generates the corresponding constraints for the SMT solver.
def generate_constraints(X, propagation_trail):
    fun = [] # List to hold the generated constraints
    for term in propagation_trail: # Iterate through each term in the propagation trail
        temp = [] 
        for i in range(len(term)): 
            if term[i] == '1': # If the term is '1', we append the negation of the corresponding variable to temp
                temp.append('(' + '~' + X[i] + ')') 
            elif term[i] == '0': # If the term is '0', we append the variable itself to temp
                temp.append(X[i]) 
        fun.append('(' + "|".join(temp) + ')')  # Join the elements in temp with '|' to make a Sum and append to fun 
    constraint = 'ASSERT ' + '&'.join(fun) + '= 0bin1' + ';\n' # Join the elements in fun with '&' to create the final PoS constraint and return it
    return constraint


"""
right_shift: represent rotate right
order: represent an array
num: represent shift bit
"""


def right_shift(order, num):
    return order[num:] + order[:num] # Rotate the list 'order' to the right by 'num' positions and return the new order


"""
left_shift: represent rotate left
order: represent an array
num: represent shift bit
"""

# Rotate the list 'order' to the left by 'num' positions and return the new order
def left_shift(order, num):
    return order[-num:] + order[:-num] 


"""
"""

# Enforcing the constraint of signed difference on the value of variable. Eg - A 1 variable can never have
# v,d = 0,1 or 0 can never have v,d = 1, -.
def derive_cond(block_size, in_var_x, in_var_v_x, in_var_d_x):
    eqn = ""
    for i in range(block_size): # Iterate through each bit position in the block
        temp = [in_var_x[i], in_var_v_x[i], in_var_d_x[i]] 
        eqn += generate_constraints(temp, derive_cond_constrain) 
    return eqn

# Enforcing the constraint of modular addition on the variables value themselves.
def modadd_value(block_size, a, b, c, v):
    eqn = " ASSERT %s = 0bin0;\n" % c[0] # Initial condition: the carry-in for the least significant bit is 0
    for i in range(block_size):
        temp = [a[i], b[i], c[i], v[i], c[i + 1]]
        eqn += generate_constraints(temp, modular_addition_value_constrain)
    return eqn

# Constraints for expansion of modular differences with two methods, flag is actually op_2 (for E) or 
# op_5 (for A) or op_6 for W.
def expand_model(block_size, in_var_v, in_var_d, c_var_v, c_var_d, out_var_v, out_var_d, flag):
    """
    if flag ==1: model the expansion of the signed difference
    (in_var_v, in_var_d): z[i]
    (c_var_v, c_var_d): c[i]
    (out_var_v, out_var_d): z'[i]
    (c_var_v, c_var_d): c[i+1]

    if flag != 1: model 0=x-y (another expansion)
    (in_var_v, in_var_d): x[i]
    (out_var_v, out_var_d): y[i]
    (c_var_v, c_var_d): c[i]
    (c_var_v, c_var_d): c[i+1]
    :param flag: different choice
    :return: expansion constrain
    """
    eqn = ""
    eqn += "ASSERT %s = 0bin0;\nASSERT %s = 0bin0;\n" % (c_var_v[0], c_var_d[0]) # initial condition
    if flag == 1: # model the expansion of the signed difference
        for i in range(block_size):
            temp = [in_var_v[i], in_var_d[i],
                    c_var_v[i], c_var_d[i],
                    out_var_v[i], out_var_d[i],
                    c_var_v[i + 1], c_var_d[i + 1]]
            eqn += generate_constraints(temp, expand_model_constrain_1)
    else:
        for i in range(block_size):
            temp = [out_var_v[i], out_var_d[i],
                    in_var_v[i], in_var_d[i],
                    c_var_v[i], c_var_d[i],
                    c_var_v[i + 1], c_var_d[i + 1]]
            eqn += generate_constraints(temp, expand_model_constrain_2)
    return eqn

# Constraints for modular addition of signed differences.
def addition_function(block_size, in_var_v_0, in_var_d_0,
                      in_var_v_1, in_var_d_1,
                      in_var_c_v, in_var_c_d,
                      out_var_v, out_var_d):
    """
    model z=x+y
    (in_var_v_0, in_var_d_0): x[i]
    (in_var_v_1, in_var_d_1): y[i]
    (in_var_c_v, in_var_c_d): carry[i]
    (out_var_v, out_var_d): z[i]
    (in_var_c_v, in_var_c_d): carry[i+1]
    :return: addition constrain
    """
    eqn = "ASSERT %s = 0bin0;\n" % (in_var_c_v[0]) # initial condition: the carry-in for the least significant bit is 0 
    eqn += "ASSERT %s = 0bin0;\n" % (in_var_c_d[0]) # initial condition: the carry-in for the least significant bit is 0
    for i in range(block_size):
        temp = [in_var_v_0[i], in_var_d_0[i],
                in_var_v_1[i], in_var_d_1[i],
                in_var_c_v[i], in_var_c_d[i],
                out_var_v[i], out_var_d[i],
                in_var_c_v[i + 1], in_var_c_d[i + 1]]
        eqn += generate_constraints(temp, modular_addition_constrain) 
    return eqn

# Constraints for XOR
def xor_function(block_size, in_var_v_0, in_var_d_0, in_var_v_1, in_var_d_1, in_var_v_2, in_var_d_2, out_var_v,
                 out_var_d, in_var_0, in_var_1, in_var_2):
    """
    these constrains only correspond to how to capture the conditions
    model w=x^y^z
    (in_var_v_0, in_var_d_0): x[i]
    (in_var_v_1, in_var_d_1): y[i]
    (in_var_v_2, in_var_d_2): z[i]
    (out_var_v, out_var_d): w[i]
    in_var_0, in_var_1, in_var_2  : value (monitoring variables)
    """
    eqn = ""
    for i in range(block_size):
        temp = [in_var_v_0[i], in_var_d_0[i],
                in_var_v_1[i], in_var_d_1[i],
                in_var_v_2[i], in_var_d_2[i],
                out_var_v[i], out_var_d[i],
                in_var_0[i], in_var_1[i], in_var_2[i]]
        eqn += generate_constraints(temp, xor_full_constrain)
    return eqn

# Constraints for MAJ
def maj_function(block_size, in_var_v_0, in_var_d_0, in_var_v_1, in_var_d_1, in_var_v_2, in_var_d_2, out_var_v,
                 out_var_d, in_var_0, in_var_1, in_var_2):
    """
    these constrains only correspond to how to capture the conditions
    model w=(x^y)&(y^z)&(x^z)
    (in_var_v_0, in_var_d_0): x[i]
    (in_var_v_1, in_var_d_1): y[i]
    (in_var_v_2, in_var_d_2): z[i]
    (out_var_v, out_var_d): w[i]
    in_var_0, in_var_1, in_var_2  : value (monitoring variables)
    """
    eqn = ""
    for i in range(block_size):
        temp = [in_var_v_0[i], in_var_d_0[i],
                in_var_v_1[i], in_var_d_1[i],
                in_var_v_2[i], in_var_d_2[i],
                out_var_v[i], out_var_d[i],
                in_var_0[i],
                in_var_1[i],
                in_var_2[i]]
        eqn += generate_constraints(temp, maj_full_constrain)
    return eqn

# Constraints for IF
def if_function(block_size, in_var_v_0, in_var_d_0, in_var_v_1, in_var_d_1, in_var_v_2, in_var_d_2, out_var_v,
                out_var_d, in_var_0, in_var_1, in_var_2):
    """
    these constrains only correspond to how to capture the conditions
    model w=(x^y)&(~x^z)
    (in_var_v_0, in_var_d_0): x[i]
    (in_var_v_1, in_var_d_1): y[i]
    (in_var_v_2, in_var_d_2): z[i]
    (out_var_v, out_var_d): w[i]
    in_var_0, in_var_1, in_var_2  : value (monitoring variables)
    """
    eqn = ""
    for i in range(block_size):
        temp = [in_var_v_1[i], in_var_d_1[i],
                in_var_v_2[i], in_var_d_2[i],
                in_var_v_0[i], in_var_d_0[i],
                out_var_v[i], out_var_d[i],
                in_var_1[i],
                in_var_2[i],
                in_var_0[i]]
        eqn += generate_constraints(temp, ifz_full_constrain)
    return eqn

# Constraint for actual boolean function on values.
def boolean_value(block_size, x0, x1, x2, out, fna):
    eqn = ""
    if fna == "MAJ":
        for i in range(block_size):
            temp = [x0[i], x1[i], x2[i], out[i]]
            eqn += generate_constraints(temp, maj_value_constrain)
    elif fna == "XOR":
        for i in range(block_size):
            temp = [x0[i], x1[i], x2[i], out[i]]
            eqn += generate_constraints(temp, xor_value_constrain)
    elif fna == "IF":
        for i in range(block_size):
            temp = [x0[i], x1[i], x2[i], out[i]]
            eqn += generate_constraints(temp, ifx_value_constrain)
    return eqn

# IMPORTANT: x variables are for A register, y variables are for E register, 
# w variables are for message word, v and d variables are for value and difference respectively.
# NOTE: Apparently, this function is just to calculate value difference of E register only, so this info comes handy later
def sha_e(block_size, __op0, __op1, __op2, step):
    # The function initiates the constraint and variable string arrays.
    # It loops 64 times (block_size for SHA-512).
    # It creates the string names for the $v$ and $d$ Boolean variables representing the signed difference of the expanded message 
    # word $W$ at the current step.
    # It appends the BITVECTOR(1) declaration to tell the SMT solver these are 1-bit Booleans.  
    eqn__constraints = []
    eqn__variable = []
    in_var_v_m = []
    in_var_d_m = []
    for j in range(block_size):
        in_var_v_m.append("wv" + "_" + str(step) + "_" + str(j))
        in_var_d_m.append("wd" + "_" + str(step) + "_" + str(j))
        eqn__variable.append("wv" + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        eqn__variable.append("wd" + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        
    # NOTE: Lists initialised, gotta see later what their names mean.
    in_var_v_a0 = [] # Input variables list for constraints
    in_var_d_a0 = []
    in_var_v_e = [] 
    in_var_d_e = []
    in_var_e = []
    
    #Define the D_i-1 register from A register of 4 steps back (A_i-4). 
    # Our aim is to get the E register of the i^th step, so we are defining the A register of the (i-4)^th step as the input. 
    for j in range(block_size):
        in_var_v_a0.append("xv" + "_" + str(step - 4) + "_" + str(j))
        in_var_d_a0.append("xd" + "_" + str(step - 4) + "_" + str(j))
        eqn__variable.append("xv" + "_" + str(step - 4) + "_" + str(j) + ": BITVECTOR(1);\n") # Creating the string to assign these variables as 1-bit Booleans in the SMT solver.
        eqn__variable.append("xd" + "_" + str(step - 4) + "_" + str(j) + ": BITVECTOR(1);\n")
        
    # Define the E_i-1 to E_i-4(= H_i-1) register from E register of 4 steps back (E_i-4).
    # NOTE : The value 4 of i is used to create the variables of signed difference of the output E_i 
    for i in range(5):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("yv" + "_" + str(step - 4 + i) + "_" + str(j))
            temp_b_d.append("yd" + "_" + str(step - 4 + i) + "_" + str(j))
            eqn__variable.append("yv" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("yd" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_e.append(temp_b_v)
        in_var_d_e.append(temp_b_d)
    
    # This is creating the variables for the value themselves
    # NOTE: Hence, we only run till i=3, because we are not calculating the final value of E_i for the full value model in this function
    # The sha_e function does not compute the raw 1s and 0s of the SHA-2 hash. 
    # It only borrows the raw value variables to act as "read-only monitors" to prevent contradictions in the IF and Sigma_1 gates.
    for i in range(4):
        temp_b = []
        for j in range(block_size):
            temp_b.append("y" + "_" + str(step - 4 + i) + "_" + str(j))
         #NOTE: We dont even create space below for E_i-4 (H register) bits in the equation that will be sent to the SMT solver because 
            # Think about how the historical registers are used in the SHA-2 step function E, F, and G are passed 
            # into the IF(E, F, G) and Sigma_1(E) functions. H is completely ignored by the Boolean functions.
            # It is only used at the very end when it is added to the sum via Modular Addition (H).
            # As we established, the "Full Model" ({C}_{full}^f) for IF and Sigma_1 strictly requires the SAT solver to track 
            # both the differences (v, d) and the underlying raw values (y) simultaneously to prevent binary contradictions.
            # If a difference passes through the IF gate, the underlying bits must mathematically support it.
            # Therefore, E, F, and G must have their raw values declared.
            # Modular addition ({C}_{Add}), however, does not. The 27-row truth table for addition relies exclusively
            # on the difference variables (v and d) and the carry variables. The raw 1s and 0s of the H register are mathematically
            # irrelevant to finding a valid difference path through an addition block.
        if i > 0: 
            for j in range(block_size):
                eqn__variable.append("y" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_e.append(temp_b)

# NOTE: THis is creating the variables for the intermediary buffer steps B_0 to B_5, one for each operation in the E register computation.
    in_var_v_b = []
    in_var_d_b = []
    for i in range(0, 6):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("bv" + str(i) + "_" + str(step) + "_" + str(j))
            temp_b_d.append("bd" + str(i) + "_" + str(step) + "_" + str(j))
            eqn__variable.append("bv" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("bd" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_b.append(temp_b_v)
        in_var_d_b.append(temp_b_d)

# This is creating the variables for the carry chains, C_0 to C_4, one for each addition in the E register computation.
    in_var_v_c = []
    in_var_d_c = []
    for i in range(5):
        temp_c_v = []
        temp_c_d = []
        for j in range(block_size + 1): # We need one extra carry bit for the carry-out of the most significant bit in the addition.
            temp_c_v.append("cv" + str(i) + "_" + str(step) + "_" + str(j))
            temp_c_d.append("cd" + str(i) + "_" + str(step) + "_" + str(j))
            eqn__variable.append("cv" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("cd" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_c.append(temp_c_v)
        in_var_d_c.append(temp_c_d)
        
# NOTE: OP0 acts as flag to determine whether we are generating and enforcing the Sigma_1 function constraints with the XOR-based full model or
# if we are skipping them for the step(Do it only if you are certain the E register has zero difference in a step)4

# The Sigma_1(E) calculation: in_var_e[3] is the current E register. The code simulates the bitwise
# right shifts (14, 18, 41) using array slicing. It passes both the difference variables (v, d)
# and the value variables (in_var_e) to the xor_function.The resulting differences are permanently mapped to the intermediate buffer B[0].
    if __op0 == 1:
        eqn__constraints.append(xor_function(block_size,
                                             right_shift(in_var_v_e[3], 14), right_shift(in_var_d_e[3], 14),
                                             right_shift(in_var_v_e[3], 18), right_shift(in_var_d_e[3], 18),
                                             right_shift(in_var_v_e[3], 41), right_shift(in_var_d_e[3], 41),
                                             in_var_v_b[0], in_var_d_b[0],
                                             right_shift(in_var_e[3], 14),
                                             right_shift(in_var_e[3], 18),
                                             right_shift(in_var_e[3], 41)))
        
# OP1 acts as flag to determine whether we are generating and enforcing the IF function constraints with the IF full model
    if __op1 == 1:
    # The IF(E, F, G) calculation: It feeds E (e[3]), F (e[2]), and G (e[1]) into
    # the if_function constraint generator. The resulting differences are mapped to buffer B[1].
        eqn__constraints.append(if_function(block_size,
                                            in_var_v_e[3], in_var_d_e[3],
                                            in_var_v_e[2], in_var_d_e[2],
                                            in_var_v_e[1], in_var_d_e[1],
                                            in_var_v_b[1], in_var_d_b[1],
                                            in_var_e[3],
                                            in_var_e[2],
                                            in_var_e[1]))

# Now, the code sequences the modular additions using the 27-row truth table {C}_{Add}.
# The SHA-512 constant K_i is completely omitted from these addition calls because constants have a difference of
# exactly zero, rendering them invisible in the Difference Model.
    eqn__constraints.append(addition_function(block_size,
                                              in_var_v_e[0], in_var_d_e[0],
                                              in_var_v_b[0], in_var_d_b[0],
                                              in_var_v_c[0], in_var_d_c[0],
                                              in_var_v_b[2], in_var_d_b[2])) # Sigma_1(E) + E_i-4 (H) -> B_2 + C_0 (carry)
    eqn__constraints.append(addition_function(block_size,
                                              in_var_v_b[2], in_var_d_b[2],
                                              in_var_v_b[1], in_var_d_b[1],
                                              in_var_v_c[1], in_var_d_c[1],
                                              in_var_v_b[3], in_var_d_b[3]))  # Sigma_1(E) + E_i-4 (H) + IF(E, F, G) -> B_3 + C_1 (carry)
    eqn__constraints.append(addition_function(block_size,
                                              in_var_v_m, in_var_d_m,
                                              in_var_v_b[3], in_var_d_b[3],
                                              in_var_v_c[2], in_var_d_c[2],
                                              in_var_v_b[5], in_var_d_b[5]))  # Sigma_1(E) + E_i-4 (H) + IF(E, F, G) + W_i -> B_5 + C_2 (carry)
    # computer Ei
    eqn__constraints.append(addition_function(block_size,
                                              in_var_v_a0, in_var_d_a0,
                                              in_var_v_b[5], in_var_d_b[5],
                                              in_var_v_c[3], in_var_d_c[3],
                                              in_var_v_b[4], in_var_d_b[4])) # Sigma_1(E) + E_i-4 (H) + IF(E, F, G) + W_i + A_i-4 (D) -> B_4 + C_3 (carry)
    
    if __op2 == 0: #This acts as a flag to switch between the two expansion models for the final E_i output. 
        #TODO: Understand the difference between the two expansion models and when to use which one.
        eqn__constraints.append(expand_model(block_size,
                                             in_var_v_b[4], in_var_d_b[4],
                                             in_var_v_c[4], in_var_d_c[4],
                                             in_var_v_e[4], in_var_d_e[4], __op2))
    else:
        eqn__constraints.append(expand_model(block_size,
                                             in_var_v_b[4], in_var_d_b[4],
                                             in_var_v_c[4], in_var_d_c[4],
                                             in_var_v_e[4], in_var_d_e[4], __op2)) 
        # Finally, the resulting E_i differences are mapped to in_var_v_e[4] and in_var_d_e[4],
        # which represent the signed difference of the E register at the current step.
    return eqn__variable, eqn__constraints


def sha_a(block_size, __op3, __op4, __op5, step):
    eqn__variable = []
    eqn__constraints = []

    # -------------------------------------------------------------------------------
    # 1. RETRIEVING THE HISTORICAL 'A' REGISTERS (TRACK 1 - DIFFERENCE MODEL)
    # -------------------------------------------------------------------------------
    in_var_v_a = []
    in_var_d_a = []
    in_var_a = []
    
    # Define the historical A registers from 4 steps back (A_i-4) up to the current step (A_i).
    # i=0 -> step-4 -> D_i-1 (Old D register)
    # i=1 -> step-3 -> C_i-1 (Old C register)
    # i=2 -> step-2 -> B_i-1 (Old B register)
    # i=3 -> step-1 -> A_i-1 (Old A register)
    # i=4 -> step   -> A_i   (The brand new A register we are calculating)
    for i in range(5):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("xv" + "_" + str(step - 4 + i) + "_" + str(j))
            temp_b_d.append("xd" + "_" + str(step - 4 + i) + "_" + str(j))
        
        # NOTE: We skip declaring the 'v' and 'd' variables for i=0 (the old D register) here.
        # Why? Because the D register's differences (xv_step-4) were ALREADY declared and appended
        # to the SMT solver inside the `sha_e` function (since E_new = D + T1). 
        # Declaring them again here would cause a duplicate variable crash in the SMT solver.
        if i > 0:
            for j in range(block_size):
                eqn__variable.append("xv" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
                eqn__variable.append("xd" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_a.append(temp_b_v)
        in_var_d_a.append(temp_b_d)

    # -------------------------------------------------------------------------------
    # 2. RETRIEVING THE RAW VALUES FOR BOOLEAN FUNCTIONS (TRACK 2 - VALUE MODEL)
    # -------------------------------------------------------------------------------
    # This loop gathers the raw 1s and 0s needed to act as "read-only monitors" for the 
    # Sigma_0 and MAJ functions to prevent binary contradictions.
    for i in range(4):
        temp_b = []
        for j in range(block_size):
            temp_b.append("x" + "_" + str(step - 4 + i) + "_" + str(j))
            
        # NOTE: We aggressively optimize RAM by skipping i=0 (the D register). 
        # The T2 calculation only uses Sigma_0(A) and MAJ(A, B, C). It completely ignores D. 
        # Because D never passes through a Boolean logic gate in this step, its raw 1s and 0s 
        # are mathematically irrelevant to the contradiction filters. 
        if i > 0:
            for j in range(block_size):
                eqn__variable.append("x" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_a.append(temp_b)

    # -------------------------------------------------------------------------------
    # 3. ALLOCATING INTERMEDIATE BUFFERS (B_5 to B_9)
    # -------------------------------------------------------------------------------
    in_var_v_b = []
    in_var_d_b = []
    # We create a 10-element array for the buffers, but ONLY declare indices 5 through 9 
    # to the SMT solver. 
    # CRITICAL SMT LINKAGE: Notice the string names ("bv5_" + str(step) + ...). 
    # The sha_e function calculated T1 and saved it into the string variable "bv5_...". 
    # Because we are generating the exact same string name here, the SMT solver will 
    # perfectly link the T1 calculated in sha_e directly into this sha_a function!
    for i in range(10):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("bv" + str(i) + "_" + str(step) + "_" + str(j))
            temp_b_d.append("bd" + str(i) + "_" + str(step) + "_" + str(j))
        
        # Only declare new memory for the new operations in this function (bv6 to bv9).
        if i > 4:
            for j in range(block_size):
                eqn__variable.append("bv" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
                eqn__variable.append("bd" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_b.append(temp_b_v)
        in_var_d_b.append(temp_b_d)

    # -------------------------------------------------------------------------------
    # 4. ALLOCATING CARRY CHAINS (C_5 to C_7)
    # -------------------------------------------------------------------------------
    in_var_v_c = []
    in_var_d_c = []
    for i in range(8):
        temp_c_v = []
        temp_c_d = []
        for j in range(block_size + 1): # +1 to catch the 65th overflow carry bit
            temp_c_v.append("cv" + str(i) + "_" + str(step) + "_" + str(j))
            temp_c_d.append("cd" + str(i) + "_" + str(step) + "_" + str(j))
        
        # We only declare new memory for the 3 modular additions happening in this function
        if i > 4:
            for j in range(block_size + 1):
                eqn__variable.append("cv" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
                eqn__variable.append("cd" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_c.append(temp_c_v)
        in_var_d_c.append(temp_c_d)
        
    # -------------------------------------------------------------------------------
    # 5. EXECUTING THE BOOLEAN LOGIC (T2 Calculation)
    # -------------------------------------------------------------------------------
    # OP3 controls the Sigma_0(A) function. The shifts 28, 34, 39 correspond to SHA-512.
    # It takes the differences (v,d) and raw values (x) of the A register (in_var_a[3]), 
    # cross-references them via the Full Model to prevent contradictions, and stores the 
    # resulting difference in the intermediate buffer B[6].
    if __op3:
        eqn__constraints.append(xor_function(block_size,
                                             right_shift(in_var_v_a[3], 28), right_shift(in_var_d_a[3], 28),
                                             right_shift(in_var_v_a[3], 34), right_shift(in_var_d_a[3], 34),
                                             right_shift(in_var_v_a[3], 39), right_shift(in_var_d_a[3], 39),
                                             in_var_v_b[6], in_var_d_b[6],
                                             right_shift(in_var_a[3], 28),
                                             right_shift(in_var_a[3], 34),
                                             right_shift(in_var_a[3], 39)))
                                             
    # OP4 controls the MAJ(A, B, C) function. 
    # It feeds A (in_var_a[3]), B (in_var_a[2]), and C (in_var_a[1]) into the MAJ Full Model.
    # The resulting difference is stored in intermediate buffer B[7].
    if __op4:
        eqn__constraints.append(maj_function(block_size, in_var_v_a[3], in_var_d_a[3],
                                             in_var_v_a[2], in_var_d_a[2],
                                             in_var_v_a[1], in_var_d_a[1],
                                             in_var_v_b[7], in_var_d_b[7],
                                             in_var_a[3],
                                             in_var_a[2],
                                             in_var_a[1]))

    # -------------------------------------------------------------------------------
    # 6. EXECUTING THE MODULAR ADDITIONS (Using the 27-row truth table)
    # -------------------------------------------------------------------------------
    # Addition 1: Adds T1 (which is sitting in b[5] from the sha_e function) to Sigma_0(A) (b[6]).
    # The sum goes to buffer B[8]. The carries ripple through C[5].
    eqn__constraints.append(addition_function(block_size, in_var_v_b[5], in_var_d_b[5],
                                              in_var_v_b[6], in_var_d_b[6],
                                              in_var_v_c[5], in_var_d_c[5],
                                              in_var_v_b[8], in_var_d_b[8]))

    # Addition 2: Adds the previous sum (b[8]) to MAJ(A,B,C) (b[7]).
    # This successfully calculates T1 + T2. 
    # The raw arithmetic sum goes to buffer B[9]. The carries ripple through C[6].
    eqn__constraints.append(addition_function(block_size, in_var_v_b[8], in_var_d_b[8],
                                              in_var_v_b[7], in_var_d_b[7],
                                              in_var_v_c[6], in_var_d_c[6],
                                              in_var_v_b[9], in_var_d_b[9]))
                                              
    # -------------------------------------------------------------------------------
    # 7. THE EXPANSION FILTER
    # -------------------------------------------------------------------------------
    # OP5 acts as the flag to filter the final raw arithmetic modular sum sitting in B[9].
    # The `expand_model` forces the raw carries and bits of B[9] to align with strict, 
    # physically valid signed differences ('n', 'u', '='). 
    # It deposits the final, verified difference variables straight into `in_var_a[4]`, 
    # officially completing the calculation for the new A register at the current step.
    if __op5 == 0:
        eqn__constraints.append(expand_model(block_size,
                                             in_var_v_b[9], in_var_d_b[9],
                                             in_var_v_c[7], in_var_d_c[7],
                                             in_var_v_a[4], in_var_d_a[4], __op5))
    else:
        eqn__constraints.append(expand_model(block_size,
                                             in_var_v_b[9], in_var_d_b[9],
                                             in_var_v_c[7], in_var_d_c[7],
                                             in_var_v_a[4], in_var_d_a[4], __op5))
    return eqn__variable, eqn__constraints

def message_expand(block_size, __op6, step):
    eqn__constraints = []
    eqn__variable = []
    
    # -------------------------------------------------------------------------------
    # 1. RETRIEVING THE HISTORICAL MESSAGE WORDS (TRACK 1 - DIFFERENCE MODEL)
    # -------------------------------------------------------------------------------
    in_var_v_w = []
    in_var_d_w = []
    in_var_w0 = []
    in_var_w2 = []
    
    # These indices perfectly match the SHA-512 message expansion formula requirements.
    # i=0 -> step-2  -> W_{t-2}
    # i=1 -> step-7  -> W_{t-7}
    # i=2 -> step-15 -> W_{t-15}
    # i=3 -> step-16 -> W_{t-16}
    # i=4 -> step-0  -> W_t (The new expanded word we are calculating)
    index = [2, 7, 15, 16, 0]
    
    for i in range(len(index)):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("wv" + "_" + str(step - index[i]) + "_" + str(j))
            temp_b_d.append("wd" + "_" + str(step - index[i]) + "_" + str(j))
            eqn__variable.append("wv" + "_" + str(step - index[i]) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("wd" + "_" + str(step - index[i]) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_w.append(temp_b_v)
        in_var_d_w.append(temp_b_d)
        
    # -------------------------------------------------------------------------------
    # 2. RETRIEVING RAW VALUES (TRACK 2) - AGGRESSIVE RAM OPTIMIZATION
    # -------------------------------------------------------------------------------
    # Notice we ONLY declare raw value ('w') variables for step-2 (W_{t-2}) and step-15 (W_{t-15}).
    # Why? Because only W_{t-2} and W_{t-15} pass through Boolean XOR gates (sigma_1 and sigma_0).
    # W_{t-7} and W_{t-16} are ONLY used in modular addition. As we proved earlier, modular 
    # addition does not need raw values to prevent contradictions. This saves 128 variables per step!
    for j in range(block_size):
        in_var_w0.append("w" + "_" + str(step - 2) + "_" + str(j))
        eqn__variable.append("w" + "_" + str(step - 2) + "_" + str(j) + ": BITVECTOR(1);\n")
    for j in range(block_size):
        in_var_w2.append("w" + "_" + str(step - 15) + "_" + str(j))
        eqn__variable.append("w" + "_" + str(step - 15) + "_" + str(j) + ": BITVECTOR(1);\n")

    # -------------------------------------------------------------------------------
    # 3. ALLOCATING INTERMEDIATE BUFFERS AND CARRY CHAINS
    # -------------------------------------------------------------------------------
    in_var_v_b = []
    in_var_d_b = []
    for i in range(5):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("mbv" + str(i) + "_" + str(step) + "_" + str(j))
            temp_b_d.append("mbd" + str(i) + "_" + str(step) + "_" + str(j))
            eqn__variable.append("mbv" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("mbd" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_b.append(temp_b_v)
        in_var_d_b.append(temp_b_d)
        
    in_var_v_c = []
    in_var_d_c = []
    for i in range(4):
        temp_c_v = []
        temp_c_d = []
        for j in range(block_size + 1):
            temp_c_v.append("mcv" + str(i) + "_" + str(step) + "_" + str(j))
            temp_c_d.append("mcd" + str(i) + "_" + str(step) + "_" + str(j))
            eqn__variable.append("mcv" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("mcd" + str(i) + "_" + str(step) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_c.append(temp_c_v)
        in_var_d_c.append(temp_c_d)
        
    # -------------------------------------------------------------------------------
    # 4. THE LOGICAL RIGHT SHIFT (SHR) ZERO-PADDING ARRAYS
    # -------------------------------------------------------------------------------
    # SHA-2 uses Circular Rotations (ROTR) AND Logical Right Shifts (SHR).
    # A circular rotation moves bits from the end to the front. A logical shift moves bits 
    # to the right, but pushes absolute ZEROS into the empty spaces at the front.
    temp_v0, temp_d0, temp_v1, temp_d1, temp_0, temp_1 = [], [], [], [], [], []
    
    # Create 6 bits of padding for the SHR(6) in sigma_1
    for i in range(6):
        temp_v0.append("temp0v" + "_" + str(step) + "_" + str(i))
        temp_d0.append("temp0d" + "_" + str(step) + "_" + str(i))
        temp_0.append("temp0" + "_" + str(step) + "_" + str(i))
        eqn__variable.append("temp0v" + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        eqn__variable.append("temp0d" + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        eqn__variable.append("temp0" + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        
    # Create 7 bits of padding for the SHR(7) in sigma_0
    for i in range(7):
        temp_v1.append("temp1v" + "_" + str(step) + "_" + str(i))
        temp_d1.append("temp1d" + "_" + str(step) + "_" + str(i))
        temp_1.append("temp1" + "_" + str(step) + "_" + str(i))
        eqn__variable.append("temp1v" + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        eqn__variable.append("temp1d" + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        eqn__variable.append("temp1" + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        
    # CRITICAL: We rigorously force all these temp padding variables to mathematically equal 0. 
    # In difference variables (v=0, d=0 means "=" which is no difference). 
    # In raw values, it means a physical bit of 0.
    for i in range(6):
        temp = "ASSERT %s = 0bin0;\n" % temp_v0[i]
        temp += "ASSERT %s = 0bin0;\n" % temp_d0[i]
        temp += "ASSERT %s = 0bin0;\n" % temp_0[i]
        eqn__constraints.append(temp)
    for i in range(7):
        temp = "ASSERT %s = 0bin0;\n" % temp_v1[i]
        temp += "ASSERT %s = 0bin0;\n" % temp_d1[i]
        temp += "ASSERT %s = 0bin0;\n" % temp_1[i]
        eqn__constraints.append(temp)

    # -------------------------------------------------------------------------------
    # 5. EXECUTING THE MATHEMATICS
    # -------------------------------------------------------------------------------
    
    # 5a. Calculate sigma_1(W_{t-2})
    # Equation: ROTR(19) XOR ROTR(61) XOR SHR(6)
    # To simulate SHR(6): `right_shift(in_var_v_w[0], 6)[:58] + temp_v0`
    # This physically shifts the array 6 times, slices off the bottom 58 bits, and glues 
    # the 6 zeroes (temp_v0) we just created to the top of the array!
    eqn__constraints.append(xor_function(block_size,
                                         right_shift(in_var_v_w[0], 19), right_shift(in_var_d_w[0], 19),
                                         right_shift(in_var_v_w[0], 61), right_shift(in_var_d_w[0], 61),
                                         right_shift(in_var_v_w[0], 6)[:58] + temp_v0,
                                         right_shift(in_var_d_w[0], 6)[:58] + temp_d0,
                                         in_var_v_b[0], in_var_d_b[0], # Output to buffer 0
                                         right_shift(in_var_w0, 19),
                                         right_shift(in_var_w0, 61),
                                         right_shift(in_var_w0, 6)[:58] + temp_0))
                                         
    # 5b. Addition 1: sigma_1(W_{t-2}) [buffer 0] + W_{t-7} [w_1]
    # Result -> buffer 1
    eqn__constraints.append(addition_function(block_size,
                                              in_var_v_b[0], in_var_d_b[0],
                                              in_var_v_w[1], in_var_d_w[1],
                                              in_var_v_c[0], in_var_d_c[0],
                                              in_var_v_b[1], in_var_d_b[1]))
                                              
    # 5c. Calculate sigma_0(W_{t-15})
    # Equation: ROTR(1) XOR ROTR(8) XOR SHR(7)
    # Output -> buffer 2
    eqn__constraints.append(xor_function(block_size,
                                         right_shift(in_var_v_w[2], 1), right_shift(in_var_d_w[2], 1),
                                         right_shift(in_var_v_w[2], 8), right_shift(in_var_d_w[2], 8),
                                         right_shift(in_var_v_w[2], 7)[:57] + temp_v1,
                                         right_shift(in_var_d_w[2], 7)[:57] + temp_d1,
                                         in_var_v_b[2], in_var_d_b[2],
                                         right_shift(in_var_w2, 1),
                                         right_shift(in_var_w2, 8),
                                         right_shift(in_var_w2, 7)[:57] + temp_1))
                                         
    # 5d. Addition 2: Previous Sum [buffer 1] + sigma_0(W_{t-15}) [buffer 2]
    # Result -> buffer 3
    eqn__constraints.append(addition_function(block_size,
                                              in_var_v_b[1], in_var_d_b[1],
                                              in_var_v_b[2], in_var_d_b[2],
                                              in_var_v_c[1], in_var_d_c[1],
                                              in_var_v_b[3], in_var_d_b[3]))
                                              
    # 5e. Addition 3 (Final Calculation): Previous Sum [buffer 3] + W_{t-16} [w_3]
    # Raw output -> buffer 4
    eqn__constraints.append(addition_function(block_size, in_var_v_b[3], in_var_d_b[3],
                                              in_var_v_w[3], in_var_d_w[3],
                                              in_var_v_c[2], in_var_d_c[2],
                                              in_var_v_b[4], in_var_d_b[4]))
                                              
    # -------------------------------------------------------------------------------
    # 6. EXPANSION FILTER (The output)
    # -------------------------------------------------------------------------------
    # Takes the raw modular sum from buffer 4, rigorously verifies the valid signed 
    # difference states using the 4th carry chain (mcv_3), and deposits the final 
    # validated bits into in_var_w[4] (which corresponds to W_t, the new message word).
    if __op6 == 0:
        eqn__constraints.append(expand_model(block_size,
                                             in_var_v_b[4], in_var_d_b[4],
                                             in_var_v_c[3], in_var_d_c[3],
                                             in_var_v_w[4], in_var_d_w[4], __op6))
    else:
        eqn__constraints.append(expand_model(block_size,
                                             in_var_v_b[4], in_var_d_b[4],
                                             in_var_v_c[3], in_var_d_c[3],
                                             in_var_v_w[4], in_var_d_w[4], __op6))
    return eqn__variable, eqn__constraints


def sha2_value(block_size, fna0, fna1, step):
    eqn__constraints = []
    eqn__variable = []
    
    # -------------------------------------------------------------------------------
    # 1. MESSAGE AND CONSTANT INITIALIZATION
    # -------------------------------------------------------------------------------
    in_var_v_m = []
    in_var_d_m = []
    m = []
    c = []
    
    # Declare the Difference variables (v, d) for the message word W_i
    for i in range(block_size):
        in_var_v_m.append("wv_" + str(step) + "_" + str(i))
        eqn__variable.append("wv_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        in_var_d_m.append("wd_" + str(step) + "_" + str(i))
        eqn__variable.append("wd_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        
    # Declare the Raw Value variable ('w') for the message word W_i
    for i in range(block_size):
        m.append("w_" + str(step) + "_" + str(i))
        eqn__variable.append("w_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        
    # CRITICAL: Hardcoding the physical constants (K_i).
    # The Difference Model ignored K_i because the difference of a constant is 0.
    # The Value Model MUST use them because it is doing real addition.
    # bin(k_constant_512[step])[2:].zfill(64)[i] converts the hex constant into a 64-bit 
    # binary string and asserts it bit-by-bit into the SMT solver's memory.
    for i in range(block_size):
        c.append("constant_" + str(step) + "_" + str(i))
        eqn__constraints.append("ASSERT constant_" + str(step) + "_" + str(block_size - i - 1) + " = 0bin%s;\n" % (
            bin(k_constant_512[step])[2:].zfill(64)[i]))
        eqn__variable.append("constant_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")

    # -------------------------------------------------------------------------------
    # 2. RETRIEVING ALL REGISTER STATES (HISTORY + NEW OUTPUTS)
    # -------------------------------------------------------------------------------
    in_var_v_e, in_var_d_e, in_var_v_a, in_var_d_a = [], [], [], []
    e, a = [], []
    
    # 2a. The E Register Differences (H, G, F, E, and E_new)
    for i in range(5):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("yv" + "_" + str(step - 4 + i) + "_" + str(j))
            temp_b_d.append("yd" + "_" + str(step - 4 + i) + "_" + str(j))
            eqn__variable.append("yv" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("yd" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_e.append(temp_b_v)
        in_var_d_e.append(temp_b_d)

    # 2b. The E Register RAW VALUES
    # NOTICE: Unlike `sha_e`, this loop uses range(5), not range(4)! 
    # Why? Because `sha2_value` is actually calculating the physical output of E_new.
    # It mathematically requires the 5th variable (i=4) to store the physical 1s and 0s.
    for i in range(5):
        temp_b_v = []
        for j in range(block_size):
            temp_b_v.append("y" + "_" + str(step - 4 + i) + "_" + str(j))
            eqn__variable.append("y" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        e.append(temp_b_v)
        
    # 2c. The A Register RAW VALUES (D, C, B, A, and A_new)
    for i in range(5):
        temp_b_v = []
        for j in range(block_size):
            temp_b_v.append("x" + "_" + str(step - 4 + i) + "_" + str(j))
            eqn__variable.append("x" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        a.append(temp_b_v)

    # 2d. The A Register Differences
    for i in range(5):
        temp_b_v = []
        temp_b_d = []
        for j in range(block_size):
            temp_b_v.append("xv" + "_" + str(step - 4 + i) + "_" + str(j))
            temp_b_d.append("xd" + "_" + str(step - 4 + i) + "_" + str(j))
            eqn__variable.append("xv" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
            eqn__variable.append("xd" + "_" + str(step - 4 + i) + "_" + str(j) + ": BITVECTOR(1);\n")
        in_var_v_a.append(temp_b_v)
        in_var_d_a.append(temp_b_d)

    # -------------------------------------------------------------------------------
    # 3. THE MASTER BRIDGE (TRACK 1 MEETS TRACK 2)
    # -------------------------------------------------------------------------------
    # This is where the AI guarantees no contradictions. 
    # derive_cond injects a strict CNF clause that permanently binds the raw Value bits
    # to their designated Difference bits. If the Difference path dictates an 'n' (0 -> 1),
    # this constraint mathematically forces the raw Value bit to be exactly 0.
    eqn__constraints.append(derive_cond(block_size, m, in_var_v_m, in_var_d_m))
    
    # Bind all historical and current A registers (D, C, B, A, A_new)
    eqn__constraints.append(derive_cond(block_size, a[0], in_var_v_a[0], in_var_d_a[0]))
    eqn__constraints.append(derive_cond(block_size, a[1], in_var_v_a[1], in_var_d_a[1]))
    eqn__constraints.append(derive_cond(block_size, a[2], in_var_v_a[2], in_var_d_a[2]))
    eqn__constraints.append(derive_cond(block_size, a[3], in_var_v_a[3], in_var_d_a[3]))
    eqn__constraints.append(derive_cond(block_size, a[4], in_var_v_a[4], in_var_d_a[4]))

    # Bind all historical and current E registers (H, G, F, E, E_new)
    eqn__constraints.append(derive_cond(block_size, e[0], in_var_v_e[0], in_var_d_e[0]))
    eqn__constraints.append(derive_cond(block_size, e[1], in_var_v_e[1], in_var_d_e[1]))
    eqn__constraints.append(derive_cond(block_size, e[2], in_var_v_e[2], in_var_d_e[2]))
    eqn__constraints.append(derive_cond(block_size, e[3], in_var_v_e[3], in_var_d_e[3]))
    eqn__constraints.append(derive_cond(block_size, e[4], in_var_v_e[4], in_var_d_e[4]))

    # -------------------------------------------------------------------------------
    # 4. ALLOCATING PURE ARITHMETIC BUFFERS
    # -------------------------------------------------------------------------------
    in_var_b = []
    # 9 buffers required for the full SHA-512 step (T1 and T2 combined).
    # NOTE: There is no 'v' or 'd' here. Just pure 1s and 0s.
    for j in range(9):
        in_var_bm = []
        for i in range(block_size):
            in_var_bm.append("b" + str(j) + "_" + str(step) + "_" + str(i))
            eqn__variable.append("b" + str(j) + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        in_var_b.append(in_var_bm)

    in_var_c = []
    # 7 carry chains required for the modular additions.
    for j in range(7):
        in_var_cm = []
        for i in range(block_size + 1):
            in_var_cm.append("c" + str(j) + "_" + str(step) + "_" + str(i))
            eqn__variable.append("c" + str(j) + "_" + str(step) + "_" + str(i) + ": BITVECTOR(1);\n")
        in_var_c.append(in_var_cm)

    # -------------------------------------------------------------------------------
    # 5. EXECUTING THE RAW BINARY HASH STEP
    # -------------------------------------------------------------------------------
    # IMPORTANT: The functions `boolean_value` and `modadd_value` simulate standard 
    # physical hardware logic. They do NOT use the complex 27-row CNF truth tables. 

    # 5a. Calculate T1 
    # b[0] = Sigma_1(E) using pure bitwise XOR
    eqn__constraints.append(boolean_value(block_size, right_shift(e[3], 14), right_shift(e[3], 18), right_shift(e[3], 41), in_var_b[0], "XOR"))
    
    # b[1] = IF(E, F, G)
    eqn__constraints.append(boolean_value(block_size, e[3], e[2], e[1], in_var_b[1], fna0))
    
    # b[2] = Sigma_1(E) + IF(E, F, G)
    eqn__constraints.append(modadd_value(block_size, in_var_b[0], in_var_b[1], in_var_c[0], in_var_b[2]))
    
    # b[3] = Previous Sum (b[2]) + Message Word W_i (m)
    eqn__constraints.append(modadd_value(block_size, m, in_var_b[2], in_var_c[1], in_var_b[3]))
    
    # b[4] = Previous Sum (b[3]) + Constant K_i (c)
    eqn__constraints.append(modadd_value(block_size, c, in_var_b[3], in_var_c[2], in_var_b[4]))
    
    # b[5] = Previous Sum (b[4]) + H register (e[0]). This is the final T1 variable!
    eqn__constraints.append(modadd_value(block_size, e[0], in_var_b[4], in_var_c[3], in_var_b[5]))
    
    # 5b. Update New E Register
    # E_new (e[4]) = D register (a[0]) + T1 (b[5])
    eqn__constraints.append(modadd_value(block_size, a[0], in_var_b[5], in_var_c[4], e[4]))
    
    # 5c. Calculate T2
    # b[6] = Sigma_0(A) using pure bitwise XOR
    eqn__constraints.append(boolean_value(block_size, right_shift(a[3], 28), right_shift(a[3], 34), right_shift(a[3], 39), in_var_b[6], "XOR"))
    
    # b[7] = MAJ(A, B, C)
    eqn__constraints.append(boolean_value(block_size, a[3], a[2], a[1], in_var_b[7], fna1))
    
    # 5d. Update New A Register
    # b[8] = T1 (b[5]) + Sigma_0(A) (b[6])
    eqn__constraints.append(modadd_value(block_size, in_var_b[5], in_var_b[6], in_var_c[5], in_var_b[8]))
    
    # A_new (a[4]) = Previous Sum (b[8]) + MAJ(A, B, C) (b[7]). 
    # This officially computes T1 + T2.
    eqn__constraints.append(modadd_value(block_size, in_var_b[7], in_var_b[8], in_var_c[6], a[4]))
    
    return eqn__variable, eqn__constraints

# -------------------------------------------------------------------------------
# HELPER 1: THE STRING PARSER
# -------------------------------------------------------------------------------
def handle(s):
    # This takes a raw string from the SMT solver output. 
    # Example input: "wv_5_31 = 0b1"
    # 1. .replace("0b", "") removes the binary prefix -> "wv_5_31 = 1"
    # 2. .split(" = ") separates the variable from its boolean value -> ["wv_5_31", "1"]
    temp = s.replace("0b", "").split(" = ")
    
    # 3. .split("_") breaks the variable name into its matrix coordinates.
    # -> index = ["wv", "5", "31"] (meaning: variable wv, step 5, bit position 31)
    index = temp[0].split("_")
    
    # Returns the coordinate array and the assigned Boolean value ("0" or "1").
    return index, temp[1]


# -------------------------------------------------------------------------------
# CORE FUNCTION: THE DIFFERENCE DECODER
# -------------------------------------------------------------------------------
def get_dc(block_size, data_list, var_str, step):
    result = []
    
    # 1. SANITIZING THE RAW SOLVER OUTPUT
    # The SMT solver output contains syntax like "ASSERT( ... );". 
    # This strips away the formatting to leave just the raw variable assignments.
    data = data_list.replace("ASSERT( ", "").replace(" );", "").replace("\nInvalid.", "").split("\n")
    
    # 2. INITIALIZING THE STATE MATRICES
    # xv stores the 'v' boolean variables.
    # xd stores the 'd' boolean variables.
    # x stores the final translated character ('u', 'n', or '0').
    xv = []
    xd = []
    x = []
    
    # Builds a 2D matrix of size [step] x [block_size] initialized entirely with zeros.
    # For SHA-512, this is a [step] x 64 matrix.
    for i in range(step):
        temp_v, temp_d, temp = [], [], []
        for j in range(block_size):
            temp_v.append(0)
            temp_d.append(0)
            temp.append(0)
        xv.append(temp_v)
        xd.append(temp_d)
        x.append(temp)
        
    # 3. POPULATING THE (V, D) MATRICES
    # Iterates through every line of the sanitized solver output.
    for i in data:
        # If the line contains the target variable prefix (e.g., "xv" for A register, "wv" for Message)
        if var_str + "v" in i:
            index, value = handle(i)
            # int(index[1]) is the step number. int(index[2]) is the bit position.
            xv[int(index[1])][int(index[2])] = value
        elif var_str + "d" in i:
            index, value = handle(i)
            xd[int(index[1])][int(index[2])] = value
            
    # 4. THE CRYPTOGRAPHIC TRANSLATION LAYER
    # This loops through the populated 2D matrices and applies the fundamental 
    # (v, d) encoding rules established in the 2024 paper to recover the signed differences.
    for i in range(len(xv)):
        for j in range(block_size):
            # Rule 1: v=1, d=1 maps to 'u' (The bit flips from 1 -> 0)
            if xv[i][j] == "1" and xd[i][j] == "1":
                x[i][j] = "u"
            # Rule 2: v=0, d=0 maps to '0' (No difference. Will be formatted to '=' later)
            elif xv[i][j] == "0" and xd[i][j] == "0":
                x[i][j] = "0"
            # Rule 3: v!=d (specifically v=0, d=1) maps to 'n' (The bit flips from 0 -> 1)
            elif xv[i][j] != xd[i][j]:
                x[i][j] = "n"

    # 5. FORMATTING THE OUTPUT STRING (MSB to LSB)
    # Binary numbers are written with the Most Significant Bit (MSB) on the far left, 
    # and the Least Significant Bit (LSB, index 0) on the far right.
    for i in range(len(x)):
        temp = "%s\"" % i
        # CRITICAL: range(block_size - 1, -1, -1) loops BACKWARDS from 63 down to 0 (or 31 to 0).
        # This ensures the blueprint is printed in standard, readable binary format.
        for j in range(block_size - 1, -1, -1):
            if x[i][j] == "0":
                temp += "="  # Translates the placeholder '0' to the mathematical '=' symbol
            elif x[i][j] == "u":
                temp += "u"
            elif x[i][j] == "n":
                temp += "n"
        temp += "\","
        result.append(temp)
        
    return result


# -------------------------------------------------------------------------------
# MASTER FUNCTION: THE BLUEPRINT EXTRACTOR
# -------------------------------------------------------------------------------
def read_differential_characteristic(block_size, result_file, step):
    result = []
    print(result_file)
    
    # Opens the raw SMT output file (e.g., "res2_dc_solution.out")
    data_list = open(result_file, "r").read()
    
    # The three target variables defining the entire SHA-2 state:
    # "x" -> The A Register characteristics
    # "y" -> The E Register characteristics
    # "w" -> The Expanded Message Word characteristics
    variable_list = ["x", "y", "w"]
    
    # Loops through the three targets, extracting and translating the full 
    # matrix for each one, and appending them into the final result array.
    for var in variable_list:
        result.append(get_dc(block_size, data_list, var, step))
        result.append("") # Adds spacing between the A, E, and W blocks
        
    return result