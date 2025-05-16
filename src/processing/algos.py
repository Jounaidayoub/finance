

def Z_score_(datapoint,window=[]):
    """THis fucntion is used to calulate the score if given data point
    in specified Range(Window)"""
    ##calcualte the mean 
    mean=sum(float(x) for x in window)/len(window)
    
    ##calculate the standar deviation
    std=(sum(((float(x)-mean)**2 for x in window))/len(window))**(1/2)
    
    
    z_score=(float(datapoint)-mean)/std
    
    
    return z_score



