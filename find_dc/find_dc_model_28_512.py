import subprocess
from find_dc.configuration.unit_function_512 import *


class FunctionModel:
    def __init__(self, init_HW, steps, bounds, message_bound, message_differential, op0, op1, op2, op3, op4, op5, op6,
                 op7):
        self.__obj_value = init_HW

        self.__end_step = bounds
        self.__start_step = steps
        self.__message_bound = message_bound
        self.__message_differential = message_differential
        self.__block_size = 64

        # holds the variable declarations
        self.__declare = []

        # holds the constraints on the variables
        self.__constraints = []

        # flags from 0 to 7. as far as we understand the flags in op8 is completely useless 
        # since it only affects the msg_expand function, which really does nothing with the 
        # flag, except for 
        self.__op0 = op0
        self.__op1 = op1
        self.__op2 = op2
        self.__op3 = op3
        self.__op4 = op4
        self.__op5 = op5
        self.__op6 = op6
        self.__op7 = op7

    # helper function: appends "s: BITVECTOR(1);\n" into self.__declare
    def save_variable(self, s):
        temp = s + ": BITVECTOR(1);\n"
        if temp not in self.__declare:
            self.__declare.append(temp)
        return s

    # helper function: checks if it is __declare, if not, then append into declare
    def check_assign(self, s):
        if s not in self.__declare:
            self.__declare.append(s)

    def assign_value(self):
        # NOTE: assigns constraints that we want to be there on the differential characteristics. 
        # some of these constraints are heuristic, while others are not. the constraints of the sha
        # function itself are added by the main function.

        # message_bound: number of steps/message expansions (TODO)
        # message_differential: rounds in which differences have been injected.

        # NOTE: the message_differential rounds are chosen by hands, and are not optimally found

        # LOOP 0: sets the differences to 0 in the rounds where there's no message difference

        # the notation 0b0 is similar to 0x0 kind of stuff

        for i in range(self.__message_bound):
            if i not in self.__message_differential:
                # block_size: 64 here, since that is the word size in SHA512
                for j in range(self.__block_size):

                    # saves a variable with the name 
                    # j is the index of the bit in the string (not in the word)
                    # wv_<round>_<64-1-j>    /* in case you are as stupid as i am, this is since the string 
                    # is starting from left to right, but the leftmost bit is the highest bit in the word */

                    # save_variable returns the variable name
                    # so essentially, the variable we just declared is 0 is the constraint.
                    temp = "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("wv_" + str(i) + "_" + str(self.__block_size - 1 - j)))                     # same as above 

                    # same as above
                    temp += "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("wd_" + str(i) + "_" + str(self.__block_size - 1 - j)))
        
                    # thus, above means (v,d) = (0,0) => signed difference is =

                    # appends the constraints
                    self.__constraints.append(temp)
        
        # LOOP 1: enforces a minimum hamming weight on the injected message differences, preventing trivial
        # output of SAT solver by just returning no message differences at all

        # more exactly, it sums all the difference bits for the word (which comprises the entire )

        # A BITVECTOR can be just thought of as a bundle of wires, each holding a 0 or 1 
        # To sum stuff up, we need a 10 bit accumulator because it cannot hold the number        
        # 64, since it contains the total number of differences.
    
        # BVPLUS(10, ...) -> Sums the variables together using a 10-bit accumulator to prevent overflow.
        # BVGT(A, B)      -> Asserts that BitVector A is strictly Greater Than BitVector B.


        temp = "ASSERT BVGT(BVPLUS(10,"
        # loops through the rounds in which there is a message difference 
        for i in range(len(self.__message_differential)):

            # prints the round which they're dealing with 
            print(self.__message_differential[i])

            # goes bit by bit over the entire word
            for j in range(self.__block_size):

                # this condition closes up 
                if len(self.__message_differential) - 1 == i and j == self.__block_size - 1:

                    # 0bin000000000<value of variable wv_<round>_<64-j-1>, here @ is for concatenation

                    # the following closes the BVGT(BVPLUS(10, list of numbers), 1) which essentially means
                    # that the number of differences should be strictly greater than 1

                    temp += "0bin000000000@%s), 0bin%s);\n" % (
                        self.save_variable(
                            # NOTE: change has been made, original code in the repo has `wv_` witten however
                            # since we are supposed to be summing the differences, we should be having the 
                            # wd_ here and not wv_ and anyway wd_ is being used everywhere else
                            "wv_" + str(self.__message_differential[i]) + "_" + str(self.__block_size - 1 - j)),
                            
                            # bin(1)[2:].zfill(10) generates the 10-bit binary string for 1 ("0000000001")
                            bin(1)[2:].zfill(10)
                        )
                else:
                    # 0bin000000000<value of variable wd_<round>_<64-j-1>, here @ is for concatenation
                    temp += "0bin000000000@%s," % (
                        self.save_variable(
                            "wd_" + str(self.__message_differential[i]) + "_" + str(self.__block_size - 1 - j)))

        # simply append the constraints
        self.__constraints.append(temp)

        # LOOP 2: goes through all the bits in the word, here they aren't going through a set of rounds
        # or anything like that, just going for a single set of constraints i think

        for i in range(self.__block_size):
            # NOTE: y represents E, and x represents A, thus yd is difference in E state bit
            # and xd is difference in A state bit.  
            
            # IMP NOTE: the state 0 or 1 does not count as a difference, although it is mentioned in the 
            # differential characteristic as a requirement. differences are only those where the d value is 
            # 1, and if you look at the differential characteristic, then the mentioned constraints indeed
            # hold.

            # the following defines that the flag_x is 1 if there is difference in the bit index
            # x in either steps 13 or 14 or both. thus it constrains their values. 
            temp = "ASSERT (%s | %s) = %s;\n" % (
                self.save_variable("yd_" + str(14) + "_" + str(self.__block_size - 1 - i)),
                self.save_variable("yd_" + str(13) + "_" + str(self.__block_size - 1 - i)),
                self.save_variable("flag_" + str(self.__block_size - 1 - i)))

            # append the constraints 
            self.__constraints.append(temp)


        # LOOP 3: similar to the logic in LOOP 1, but it sets the constraint that the number of 
        # flags with value 1 is 4. This just represents the bit positions that are changing accross
        # steps 13 and 14.

        # IMP NOTE HEURISTIC: have to figure out the reason for 4 differences, and specifically in 13 & 14
        temp = "ASSERT BVPLUS(10,"
        for j in range(self.__block_size):
            if j == self.__block_size - 1:
                # bin(4)[2:].zfill(10) creates the 10-bit binary string for the number 4 ("0000000100")
                temp += "0bin000000000@%s) = 0bin%s;\n" % ("flag_" + str(j), bin(4)[2:].zfill(10))
            else:
                temp += "0bin000000000@%s," % ("flag_" + str(j))
        self.__constraints.append(temp)

        # LOOP 4: sets a maximum hamming weight on step 12, here BVLE means BitVector Less than Equal to 
        # logic is similar as in LOOP 3.
        temp = "ASSERT BVLE(BVPLUS(10,"
        for j in range(self.__block_size):
            if j == self.__block_size - 1:
                # bin(4)[2:].zfill(10) creates the 10-bit binary string for the number 4 ("0000000100")
                temp += "0bin000000000@%s), 0bin%s);\n" % ("yd_" + str(12) + "_" + str(j), bin(4)[2:].zfill(10))
            else:
                temp += "0bin000000000@%s," % ("yd_" + str(12) + "_" + str(j))
        self.__constraints.append(temp)


        # message differences are only injected at the 8th step, thus, till the step 7th,  or from
        # step 4 to step 7, there must be no differences at all in the two hash executions.
        # this is exact, and is not a heuristic. follows directly from the logic
        for step in range(4, 8):
            for i in range(self.__block_size):
                temp = "ASSERT xv_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                temp += "ASSERT xd_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                temp += "ASSERT yv_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                temp += "ASSERT yd_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                self.__constraints.append(temp)
        
        # IMP NOTE: the following choices of rounds (11 to end, 15 to end) appear to be heuristics

        # constraint of no difference in A from step 11 to the end of the rounds
        for step in range(11, self.__end_step):
            for i in range(self.__block_size):
                temp = "ASSERT xv_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                temp += "ASSERT xd_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                self.__constraints.append(temp)
        
        # constraint of no difference in E from step 15 to the end of rounds
        for step in range(15, self.__end_step):
            for i in range(self.__block_size):
                temp = "ASSERT yv_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                temp += "ASSERT yd_" + str(step) + "_" + str(i) + " = 0bin0;\n"
                self.__constraints.append(temp)


        # VERY IMP NOTE: The following might appear weird, but it follows from the section 4.4 of the paper
        
        # they mention finding the differential characteristic as a three-step process, and not a single step
        # process. 
        # 
        # step 1: they are first finding the DC of the message, keeping specifically H(Delta W_16) and H(Delta W_18)
        # minimal (TODO: Why 16 and 18? my hypothesis is since these are the only ones that are not in our control)
        #
        # step 2: with the fixed Delta W, find (Delta A, Delta E) which is valid. Now there's no clear way to do this
        # however the authors mention three possible strategies to do this.
        #   1. strategy 1: fixed Delta W, find (Delta A, Delta E) and minimize HW(Delta A). now, given this fixed
        #                  (Delta W, Delta A), find something which minimizes HW(Delta E)
        #   2. strategy 2: fixed Delta W find (Delta A, Delta E) which minimizes HW(Delta E)
        #   3. strategy 3: in above two, the HW was summed over all the rounds, however in this strategy, we will be 
        #                  still minimizing HW, but now HW to be minimized will only be over rounds 11 to 27 (later rounds)
        #
        # according to the authors, the strategy 3 is best for message modifications, since it leaves less guesswork in 
        # later rounds, leading to better convergance, and also leads to more differences initially, which can be handled
        # using the degree of freedoms of the initial words. this is better for finding the messages
        #
        # IMP NOTE: however which strategy they actually use here is somewhat unclear, it seems none of the strategies 
        # are being used as-is as mentioned in the paper. nor is the correct_dc_model phase doing things as mentioned.

        # they mention using strategy 3, but according to me, a variant of strategy 1 is being used, where Delta A is 
        # being minimized, not Delta E 

        # 10 constraints on ee, i.e. E these are added to y which corresponded to E.

        # VERY IMP NOTE: the first two rows of the ee variable do not match with the actual differential characteristic
        # however, the later rounds map perfectly. also in the correct_dc_model file, only the first 2 rows are left free
        # and the rest of the rows which have 0 differences are constrained. which makes me think that the two files at 
        # least are in-sync, but we can't say the same about the code being in sync with the research paper, since the 
        # correct_dc code fixed Delta E_10, as opposed to freeing it (paper says Delta E_8, Delta E_9, Delta E_10) should 
        # be free, and constraints for value transitions should be added for rounds 10 to 12, which at least is being done 
        # in the paper
        # 
        # 
        # moreover, the output of find_dc is not being used in correct_dc as the paper says it should. so in general there's
        # a lot of mismatch.  
        ee = ["======u=nuuuunu====nu=uunu=nn===nu=nuun=nn===nu==nu=u=n=u======u",
              "=un==unn=nnunnuun=nuuuunu=unuu===un===unununnnnnn=nn==nn=u=u==nn",
              "============u============n===================================nuu",
              "==u====unnn==n=n=n========u===u=========n==u=========u=un=======",
              "===========n=============u============u========================u",
              "============n===================================================",
              "============u============n============n========================n",
              "================================================================",
              "================================================================",
              "================================================================"]
    
        # simply assigns the given characteristics 
        for i in range(len(ee)):
            for j in range(len(ee[i])):
                if ee[i][j] == "=":
                    temp = "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("yv_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    temp += "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("yd_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    self.__constraints.append(temp)
                elif ee[i][j] == "u":
                    temp = "ASSERT %s = 0bin1;\n" % (
                        self.save_variable("yv_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    temp += "ASSERT %s = 0bin1;\n" % (
                        self.save_variable("yd_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    self.__constraints.append(temp)
                elif ee[i][j] == "n":
                    temp = "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("yv_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    temp += "ASSERT %s = 0bin1;\n" % (
                        self.save_variable("yd_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    self.__constraints.append(temp)

        # 11 constraints on ss, remember that w represented the words, so these constraints are on the word
        # also the message differences are only in the rounds 8 to 18, so that's why there are 11 constraints
        # comparing this to the research paper, these are exactly the constraints in their found dc

        # NOTE: we should try writing out something which finds us this kind of characteristic, or at least 
        # something which gives us a message characteristic. 
        ss = ["======u=nuuuunu====nu=uunu=nn===nu=nuun=nn===nu==nu=u=n=u======u",
              "=======unnnnn========nuuuu========nuuuu===========nuuuuuuuuuuuuu",
              "================================================================",
              "================================================================",
              "================================================================",
              "=========n============u============n=====================u==n===",
              "================================================================",
              "================================================================",
              "=======unnnnn====nuuuuuuuu=======nuuuuu================nuuuuuuuu",
              "================================================================",
              "============n============u============u========================u"]

        # simply assigns the given characteristics
        for i in range(len(ss)):
            for j in range(len(ss[i])):
                if ss[i][j] == "=":
                    temp = "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("wv_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    temp += "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("wd_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    self.__constraints.append(temp)
                elif ss[i][j] == "u":
                    temp = "ASSERT %s = 0bin1;\n" % (
                        self.save_variable("wv_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    temp += "ASSERT %s = 0bin1;\n" % (
                        self.save_variable("wd_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    self.__constraints.append(temp)
                elif ss[i][j] == "n":
                    temp = "ASSERT %s = 0bin0;\n" % (
                        self.save_variable("wv_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    temp += "ASSERT %s = 0bin1;\n" % (
                        self.save_variable("wd_" + str(i + 8) + "_" + str(self.__block_size - 1 - j)))
                    self.__constraints.append(temp)

    # i suppose this function just adds the constraints imposed by the sha2 hash function round propagation itself
    # on the variables. as we figured out earlier, the op0, op1, op3, op4 control XOR step in A, IF, XOR step in E,
    # and MAJ functions respectively. looking at the values passed on to the function, they are being added at each
    # of the steps here in any case. 

    # op2 and op5 are more interesting, and they appear to be toggling between the two modes of the expand_model fn
    # which is very interesting, since that does not appear to do anything at all. 
    # 
    # def expand_model(block_size, in_var_v, in_var_d, c_var_v, c_var_d, out_var_v, out_var_d, flag):
    #     """
    #     if flag ==1: model the expansion of the signed difference
    #     (in_var_v, in_var_d): z[i]
    #     (c_var_v, c_var_d): c[i]
    #     (out_var_v, out_var_d): z'[i]
    #     (c_var_v, c_var_d): c[i+1]

    #     if flag != 1: model 0=x-y (another expansion)
    #     (in_var_v, in_var_d): x[i]
    #     (out_var_v, out_var_d): y[i]
    #     (c_var_v, c_var_d): c[i]
    #     (c_var_v, c_var_d): c[i+1]
    #     :param flag: different choice
    #     :return: expansion constrain
    #     """
    #     eqn = ""
    #     eqn += "ASSERT %s = 0bin0;\nASSERT %s = 0bin0;\n" % (c_var_v[0], c_var_d[0])
    #     if flag == 1:
    #         for i in range(block_size):
    #             temp = [in_var_v[i], in_var_d[i],
    #                     c_var_v[i], c_var_d[i],
    #                     out_var_v[i], out_var_d[i],
    #                     c_var_v[i + 1], c_var_d[i + 1]]
    #             eqn += generate_constraints(temp, expand_model_constrain_1)
    #     else:
    #         for i in range(block_size):
    #             temp = [out_var_v[i], out_var_d[i],
    #                     in_var_v[i], in_var_d[i],
    #                     c_var_v[i], c_var_d[i],
    #                     c_var_v[i + 1], c_var_d[i + 1]]
    #             eqn += generate_constraints(temp, expand_model_constrain_2)
    #     return eqn 
    
    # NOTE: this only adds the round based constraints on the rounds on which there are differences, since there is 
    # no difference from steps 0 to 7, adding round propagation constraints on the steps 0 to 7 is redundant.

    def main(self):
        for i in range(self.__start_step, self.__end_step):
            # add the constraints on E for round i
            variable_e, constrain_e = sha_e(self.__block_size, self.__op0[i], self.__op1[i], self.__op2[i], i)
            self.__constraints.append("".join(constrain_e))

            # make sure the variables in the round are all added to the declaration (the part holding all the variables)
            # only once to ensure syntax
            for var in variable_e:
                self.check_assign(var)

            # add the constraints on A for round i
            variable_a, constrain_a = sha_a(self.__block_size, self.__op3[i], self.__op4[i], self.__op5[i], i)
            self.__constraints.append("".join(constrain_a))

            # same stuff as before
            for var in variable_a:
                self.check_assign(var)

        for i in range(self.__message_bound):
            if i > 15:
                # same as before, only starts happening at round 17 (note, indexing is from 0)
                variable_w, constrain_w = message_expand(self.__block_size, self.__op6[i], i)
                self.__constraints.append("".join(constrain_w))

                # same as before
                for var in variable_w:
                    self.check_assign(var)


    # this is the function to build a constraint which sets the hamming weight of the Delta A registers equal to the 
    # passed parameter value obj

    # NOTE: this does not actually adds the constraint, it just builds it. 
    def obj_value(self, obj):
        temp = "ASSERT BVPLUS(10,"
        for i in range(self.__start_step, self.__end_step):
            for j in range(self.__block_size):
                if i == self.__end_step - 1 and j == self.__block_size - 1:
                    temp += "0bin000000000@%s) = 0bin%s;\n" % ("xd_" + str(i) + "_" + str(j), bin(obj)[2:].zfill(10))
                else:
                    temp += "0bin000000000@%s," % ("xd_" + str(i) + "_" + str(j))
        return temp

    def solver(self):
        # generate all round-constraints
        self.main()

        # generate all modelling constraints
        self.assign_value()
        constrain = "".join(self.__constraints)
        variable = "".join(self.__declare)

        # an STP-prover has two components, one is ASSERT and other is QUERY which is a statement whose truth
        # value is being asked about, i.e. it is being aske whether it is always true conditioned on all the 
        # ASSERT values. thus, the question being asked in the follwoing query is "if all the assert statements 
        # hold true, then false is always true". thus, if the prover finds a valid set of variables which gives
        # all the assert statements as true, then the query immediately is false, since false is not always true.
        # however, if the prover goes through the entire search space and finds no value which makes all the
        # assert statements true, then the claim false is always true is justified immediately, since condition 
        # on which its truth value was based is not true, so it mathematically is correct, that false is always
        # true. hence, when it does prove the query false, it will dump the counter-example, which will give 
        # us a differential characteristic. however, if it says the query is "Valid.\n", then no set of vars
        # could be found which make all the assert statements true.
        query = '\n' + 'QUERY FALSE;\nCOUNTEREXAMPLE;'

        # lowest hamming weight found
        kk = -1

        # start at initial hw 
        for obj_val in range(self.__obj_value, -1, -1):
            # create .cvc file
            file_write = open("find_dc_model.cvc", "w")

            # generate constraints which make the HW of Delta A as target
            obj = self.obj_value(obj_val)

            # adds the declared variables
            file_write.write(variable)
            
            # adds the generated constraints
            file_write.write(constrain)

            # adds the constraint on hamming weight of Delta A 
            file_write.write(obj)
            file_write.write(query)
            file_write.close()

            # just solves, refer to logic about COUNTEREXAMPLE.
            stp_parameters = ["stp", "find_dc_model.cvc", "--cryptominisat", "--threads", "26"]
            R = subprocess.check_output(stp_parameters)
            if "Valid.\n" != R.decode():
                file = open("res2_dc_solution_" + str(obj_val) + ".out", "w")
                file.write(R.decode())
                file.close()
                print("The number of HW in a differential characteristic is %s: valid" % obj_val)
                kk = obj_val

            else:
                print("The number of HW in a differential characteristic is %s: invalid" % obj_val)
                break
        if kk != -1:
            for temp in read_differential_characteristic(self.__block_size,
                                                         "res2_dc_solution_" + str(kk) + ".out",
                                                         self.__message_bound):
                for tt in temp:
                    print(tt)


if __name__ == '__main__':
    start_step = 8
    end_step = 19
    message_bound = 28
    init_HW = 100

    # these are chosen since there are very few words which do not cause utter chaos
    # TODO: have to explictly lay-out the reasoning for this in the explanation part.
    message_differential = [8, 9, 13, 16, 18]
    
    # controls XOR for E
    op0 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    # controls IF function
    op1 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    # toggles the expand_model function (seems redundant)
    op2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    # controls XOR for A
    op3 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    # controls MAJ function
    op4 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    # toggles the expand_model function (seems redundant)
    op5 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    op6 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # adds constraints to the actual values of the hash state, and not just the differences
    op7 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # NOTE: really confused how this happens, since we probably would need the value transitions
    # to also be modelled parallely, which now that i think about it, has been mentioned in the paper 
    # somewhere

    # just calls the functioon model, and solves
    FunctionModel(init_HW, start_step, end_step, message_bound, message_differential, op0, op1, op2, op3, op4, op5, op6,
                  op7).solver()
