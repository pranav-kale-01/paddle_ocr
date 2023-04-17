import configparser
import re   

def regex_final(ocr_text):
    try:
        final_batch_no = ""
        batch_no = []
        batch_no_regex = []
        opt = []

        # getting the regex patterns from the regex_pattern.ini file
        config = configparser.ConfigParser()
        config.read('./config/last_regex_pattern.ini')

        for i in config:
            if i == 'DEFAULT':
                pass
            else:
                opt.append(i)

        options = config.options(opt[0])

        for i in options:
            batch_no_regex.append(config.get(opt[0], i))

        ls = ocr_text.split("^")

        # we will then each string to remove the trailing \n
        for i in ls:
            i.rstrip("\n")

        # print( ls )
        # looping through each line of the file
        for j in ls:
            val = re.search(batch_no_regex[0], j, re.IGNORECASE)
            alp_num = re.search(batch_no_regex[3], j, re.IGNORECASE)
            sp_chars = re.search( '[@_!#$%^&*()<>?/\|}{~:]', j, re.IGNORECASE )
            only_num = re.search( '^[0-9]', j)

            # searching for commonly used abbrevations for batch number like, batch. no. b. no, etc.
            if (val):
                # checking if the remaining string contains any other data (like MFD MRP) or just the batch no.
                val2 = re.search(batch_no_regex[1], val.string[val.span()[1]:], re.IGNORECASE)
                sp_chars = re.search( '[@_!#$%^&*()<>?/\|}{~:]', val.string[val.span()[1]:], re.IGNORECASE )

                if (val2 and not sp_chars ):
                    batch_no.append( { val.string[val.span()[1]: val.span()[1] + val2.span()[0]] : 6 })
                else:
                    # print("Test", val.string[val.span()[1]:])
                    if (len(val.string[val.span()[1]:]) != 0):
                        if (val.string[val.span()[1]:]):
                            batch_no.append( { val.string[val.span()[1]:] : 4 })

            elif( alp_num and len( alp_num.string ) <= 10  ):
                # check for commonly used workds
                reg1 = re.search(batch_no_regex[1], j, re.IGNORECASE)
                # reg2 = re.search(batch_no_regex[2], j, re.IGNORECASE)

                # if( reg1 ):
                #     print( "reg1", reg1.string )

                if( not reg1 ):
                    batch_no.append( {alp_num.string : 5 } )
                else:
                    batch_no.append( {alp_num.string : 4 } )

            elif( only_num and len(only_num.string) > 3 ):
                batch_no.append( { only_num.string : 3 })

            elif( not sp_chars ):
                # this means that the string does not starts with bno, batch no, etc. but also does not contain any special characters

                # checking for a string which does not contain some commonly found words like mg, tablets, or month name etc.
                val3 = re.search(batch_no_regex[2], j, re.IGNORECASE)

                if (val3):
                    # checking for a alpha numeric string
                    val4 = re.search(batch_no_regex[3], j, re.IGNORECASE)

                    if (val4):
                        # checking if the remaining string contains any other data (like MDF MRP) or just the batch no.
                        val5 = re.search(batch_no_regex[1], val4.string, re.IGNORECASE)

                        if ( val5 and val4.string[val4.span()[0]: val4.span()[1] + val5.span()[0]]):

                            print( val4.string[val4.span()[0]: val4.span()[1] + val5.span()[0]] )

                            batch_no.append( { val4.string[val4.span()[0]: val4.span()[1] + val5.span()[0]] : 2 })

                else:
                    # checking for a literal that is a combination of characters and numbers and does not contains any other special symbols except hypen (-)
                    val5 = re.search(batch_no_regex[3], j, re.IGNORECASE)

                    if (val5):
                        # checking if the remaining string contains any other data (like MFD MRP) or just the batch no.
                        val6 = re.search(batch_no_regex[1], val5.string, re.IGNORECASE)

                        if (val6 and val5.string[val5.span()[0]: val5.span()[1] + val6.span()[0]]):
                            #checking if the remaining string is non-empty
                            if (val5.string[ val5.span()[0]  :  val5.span()[1] ] ):

                                batch_no.append( { val5.string[val5.span()[0]: val5.span()[1]] : 2 })

        # print( batch_no )
        # if the batch number is not empty then assigning it to final batch no.
        if( len(batch_no) > 0 ):
            b_no = ""
            accuracy = 0
            for i in batch_no:
                item_name = list(i.keys())[0]

                if( i[item_name] >= accuracy ):
                    b_no = item_name
                    accuracy = i[item_name]

            if( b_no != "" ):
                final_batch_no = b_no.strip(".")
                return final_batch_no

    except Exception as e:
        print('exception in regex final: ' + str(e))
        raise e


# file = open('D:/results.txt', 'r')
# text = file.readlines()
# for i in text:
#     temp = i.split("-", maxsplit= 1)[-1].strip()
#     temp = temp.split("-", maxsplit= 1)[0].strip()
    
#     print( "final - ",regex_final( temp, "./output") )