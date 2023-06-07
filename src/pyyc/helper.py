## we all add the helper functions here to use acrosss files ###

def tempVar(body = 'tmp'):
        ## generate temporary variables
        if not hasattr(tempVar, "counter"):
            tempVar.counter = 0
        tempVar.counter += 1
        return body + "_" + str(tempVar.counter)

