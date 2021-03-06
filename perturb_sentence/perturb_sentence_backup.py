from gensim.models import Word2Vec
from random import randint
import random
import string
from copy import deepcopy
import black_box
import numpy
import math
import linear_classifier
import tensorflow as tf

#TODO switch back to my_svm2
#svm_classifier = linear_classifier.load_classifier('my_svm2')
svm_classifier = linear_classifier.load_classifier('my_svm')

model = Word2Vec.load("new_model")
num_features = 300

#TODO figure out the actual Y classification values of this
spam = [1,0]
ham = [0,1]

#START RANDOM PERTURBATION SECTION
#This section contains code that will perturb a sentence randomly.

#This method will perturb a sentence and return a perturbed version with changed words highlighted in red
#using ANSI surrounding characters.  Input and output are string lists.
#User is requested to select number of words and features to perturb, as well as distance in the vector space.
#The words and features to perturb are then chosen randomly and the sentence is perturbed.
def randomPerturbation(classifier, sentence_list, num_words_to_perturb, num_features_to_perturb, distance_to_perturb):
    
    #perturbed_word_indexes = choose_words_to_perturb(num_words_to_perturb, sentence_list)
    perturbed_word_indexes = choose_words_to_perturb2(classifier, num_words_to_perturb, sentence_list)
    
    perturbed_list = perturb_words(sentence_list, perturbed_word_indexes, num_features_to_perturb, distance_to_perturb)
            
    colored_perturbed_list = color_words_red(perturbed_list, perturbed_word_indexes)
    return colored_perturbed_list
	
def get_loss(classifier, sentence_vector, word_vector):
    sentence_classification = linear_classifier.get_classification(classifier, [sentence_vector])[0]
    word_classification = linear_classifier.get_classification(classifier, [word_vector])[0]
    if(sentence_classification == word_classification):
        print("It's 0")
        loss = 0
    else:
        print("It's not 0")
        loss = 1
    return loss

#TODO figure this out and integrate with all three	
def choose_words_to_perturb2(checkpoint_dir, num_words_to_perturb, sentence_string):
    vocab_path = checkpoint_dir + 'vocab'
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform(sentence_string)))


#This will take an integer number of words to perturb and a string list sentence
#It will return a list of indexes to perturb for the sentence.
#The indices are chosen randomly.  If the user tries to perturb more than the
#maximum number of words in the sentence, all words will be perturbed.
def choose_words_to_perturb(num_words_to_perturb, sentence_list):
    perturbed_word_indexes = []
    if(num_words_to_perturb > len(sentence_list)):
        num_words_to_perturb = len(sentence_list)
    flag = False
    
    for x in range(0, num_words_to_perturb):
        while(flag == False):
            word_index = randint(0, len(sentence_list) - 1)
            if(word_index not in perturbed_word_indexes):
                flag = True
                perturbed_word_indexes = perturbed_word_indexes + [word_index]
        flag = False
    return perturbed_word_indexes    

#this method chooses features randomly to perturb.  It takes as input an integer
#number of features to perturb and randomly creates a list of indexes of that size.    
def choose_features_to_perturb(num_features_to_perturb, total_features):
    perturbed_feature_indexes = []
    flag = True
    for y in range(0, num_features_to_perturb + 1):
        while(flag == False):
            feature_index = randint(0, total_features - 1)
            if(feature_index not in perturbed_feature_indexes):
                flag = True
                perturbed_feature_indexes = perturbed_feature_indexes + [feature_index]
        flag = False
    return perturbed_feature_indexes
	
#END RANDOM PERTURBATION SECTION

#TODO FIX TO CNN
def sum_of_vector_logs(vector1, vector2):
    vector3 = vector1
    for key, feature in enumerate(vector1):
        if(feature > 0 and feature != -0.0 and vector2[key] > 0 and vector2[key] != -0.0):
            vector3[key] = math.log1p(feature) + math.log1p(vector2[key])
        elif((feature < 0 or feature == -0.0) and vector2[key] > 0 and vector2[key] != -0.0):
            vector3[key] = -math.log1p(-feature) + math.log1p(vector2[key])
        elif(feature > 0 and feature != -0.0 and (vector2[key] < 0 or vector2[key] == -0.0)):
            vector3[key] = math.log1p(feature) - math.log1p(-vector2[key])
        else:
            vector3[key] = -math.log1p(-feature) - math.log1p(-vector2[key])
        
    return vector3
    
def multiply_sentence(sentence):
    product = [1.0]*300
    for key, word in enumerate(sentence):
        if(key > 39):
            break
        if(word in model):
            word_vector = deepcopy(model[word.lower()])
        else:
            word_vector = [1.0]*300
        product = sum_of_vector_logs(product, word_vector)
        
    return product


#TODO integrate CNN classifier	
#START ANCHOR POINTS SECTION
#This section contains the code for the anchor points algorithm
#A black box classifier is needed for this to run (currently in black_box.py)

#This is the anchor points algorithm. In this method are both the explore and exploit portions.
#An exploration budget is requested from the user, and the same budget is used for exploitation.
#A list of sentences is taken as input, and a list of perturbed sentences are created from this list to be returned.
def anchorPoints(classifier, goal_classification, sentence_list, exploration_budget):
    anchor_points = []
    search_radius = 1.0
    radius_min = .1
    radius_max = .5
    seed = sentence_list
    explore = seed
    count_legitimate = 0.0
    perturbed_sample = sentence_list[0]
    for i in range(1, exploration_budget + 1):
        exploreIndex = randint(0, len(explore) - 1)
        sample = explore[exploreIndex]
        search_radius = (radius_max - radius_min)*(count_legitimate/float(i)) + radius_min
        perturbed_sample = anchorPerturb(sample, search_radius)
        vector_sample = multiply_sentence(perturbed_sample)
        if(linear_classifier.get_classification(classifier, [vector_sample])[0] == goal_classification):
            explore = explore + [perturbed_sample]
            count_legitimate = count_legitimate + 1.0

    attack_set = []
    number_of_attacks = exploration_budget
    for i in range(1, number_of_attacks + 1):
        index1 = randint(0, len(explore) - 1)
        index2 = randint(0, len(explore) - 1)
        sample1 = explore[index1]
        sample2 = explore[index2]
        perturbed_sample1 = anchorPerturb(sample1, search_radius)
        perturbed_sample2 = anchorPerturb(sample2, search_radius)
        gamma = randint(0, 1)
        multiply1 = multiplySentence(perturbed_sample1, gamma)
        multiply2 = multiplySentence(perturbed_sample2, 1 - gamma)
        attack_set = attack_set + [addSentences(multiply1, multiply2)]
        
    return attack_set	

#This is used to perturb sentences for the anchorPoints algorithm.
#It takes a sentence as a list of string words and a floating point number
#perturbation search radius as its parameters.  It returns a
#perturbed sentence as a list of strings.
def anchorPerturb(sample, search_radius):
    perturbed_feature_indexes = []
    perturbed_list = sample[:]
    #num_features = len(deepcopy(model[sample[0].lower()]))
    for f in range(0, num_features):
        perturbed_feature_indexes = perturbed_feature_indexes + [f]
    for key, word in enumerate(sample):
        distance_to_perturb = random.uniform(-search_radius, search_radius)
        new_word = [['word', 1.0]]
        new_word[0][0] = word
        if(word.lower() in model):
            temp = deepcopy(model[word.lower()])
            #while(word.lower() == new_word[0][0].lower()):
            temp = perturb_features(temp, perturbed_feature_indexes, distance_to_perturb)
            new_word = model.similar_by_vector(temp, topn=1, restrict_vocab=None)
            perturbed_list[key] = new_word[0][0]
        else:
            print("Word " + word + " not in vocabulary") #Can't perturb a word that doesn't exist in the vocabulary
    return perturbed_list
	
#END ANCHOR POINTS SECTION
	

#TODO integrate CNN classifier
#START REVERSE ENGINEERING SECTION
#This contains the code for the reverse engineering perturbation.
#Reverse engineering code requires a linear classifier to run (currently in linear_classifier.py)


#this is the explore portion of the reverse engineering algorithm.  It takes
#a list of sentences as input.  Currently the sentence list is expected to consist
#of only one sentence.  It needs one valid and one invalid sentence.  It has a hardcoded
#portion to create the other sentence.  It returns a list:
# [trained_classifier, sentence_list] that consists of the classifier that was
#trained to try to reverse engineer the real classifier and the list of sentences
#that were explored in order to do it.
#this will request an exploration budget and magnitude from the user.
def reverseEngineeringExplore(classifier, goal_classification, sentence_list, exploration_budget, magnitude):
    print("Reverse engineering")
    perturbed_list = sentence_list[:]

    rand = generateRandomSentence(len(sentence_list), num_features)
    multiplied = multiply_sentence(rand)
    #print(len(sentence_list))
    while(linear_classifier.get_classification(classifier, [multiplied])[0] == goal_classification):
        rand = generateRandomSentence(len(sentence_list), num_features)
        multiplied = multiply_sentence(rand)
		
    legitimate_samples = [sentence_list[:]] 
    malicious_samples = [rand[:]]
	
	#TODO: this should not be hard coded
    #seed1 = sentence_list[:]
    #for word in seed1:
    #    word = word.lower()
    #seed2 = seed1[:]
    #if("the" in seed2):
    #    for word in seed2:
    #        if(word == "the"):
    #            word = "a"
    #    legitimate_samples = [seed1]
    #    malicious_samples = [seed2]
    #else:
    #    seed2[0] = "the"
    #    legitimate_samples = [seed2]
    #    malicious_samples = [seed1]
    #/TODO
        

    #num_features = len(deepcopy(model[sentence_list[0][0].lower()]))

    for i in range(1, exploration_budget + 1):
        index_legit = randint(0, len(legitimate_samples) - 1)
        sample_legit = legitimate_samples[index_legit]   
        index_malicious = randint(0, len(malicious_samples) - 1)
        sample_malicious = malicious_samples[index_malicious]
        new_sample = subtractSentences(sample_legit, sample_malicious)  
        random_sample = generateRandomSentence(len(new_sample), num_features)
        random_sample = subtractSentences(random_sample, makeOrthogonal(random_sample, new_sample))
        gamma = random.uniform(0, magnitude)
        norm = sentenceNorm(random_sample)
        multiplier = gamma / norm
        random_sample = multiplySentence(random_sample, multiplier)
        sum = addSentences(sample_legit, sample_malicious)
        multiplied_sentence = multiplySentence(sum, .5)
        midpoint_sample = addSentences(random_sample, multiplied_sentence)
        if(black_box.spam_or_non_spam2(midpoint_sample) == goal_classification):
            legitimate_samples = legitimate_samples + [midpoint_sample]
        else:
            malicious_samples = malicious_samples + [midpoint_sample]
    all_samples = legitimate_samples + malicious_samples

    #train classifier using all samples
    legitimate_train_data = sentenceListToVectors(legitimate_samples)
    legitimate_labels = makeLabels(len(legitimate_train_data), goal_classification)
    malicious_train_data = sentenceListToVectors(malicious_samples)

    multiplied_data = []
    for data in malicious_train_data:
        multiplied_data = multiplied_data + [multiply_sentence(data)]
    malicious_labels = linear_classifier.get_classification(classifier, multiplied_data)
    malicious_labels = list(map(int, malicious_labels))
    #print("Malicious:")
    #print(malicious_labels)
    #print("Legitimate:")
    #print(legitimate_labels)
    #for data in malicious_samples:
    #    malicious_labels = malicious_labels + 
    #malicious_labels = makeLabels(len(malicious_train_data), 'spam')
    train_data = legitimate_train_data + malicious_train_data
    labels = legitimate_labels + malicious_labels
    trainedClassifier = linear_classifier.train_classifier(train_data, labels)

    return [trainedClassifier, all_samples]

#This is the exploit portion of the reverse engineering algorithm.	It takes a trained
#classifier (scikit_learn svm) and a set of perturbed sentences produced by the explore
#portion.  It returns the set of sentences for the attack list.
def reverseEngineeringExploit(classifier, goal_classification, perturbed_sentences, exploitation_budget):
    sentences = perturbed_sentences
    sentences = anchorPoints2(classifier, goal_classification, perturbed_sentences, exploitation_budget)
    return sentences

#This is a duplicate of the anchor points method.  It is held separate due to changes to make it
#specific to the reverse engineering algorithm.  It is used in the exploit portion of reverse engineering.
#It takes a trained linear classifier (currently created by scikit_learn's svm) 
#and a list of sentences as input.  The list of sentences
#is created by the explore portion of the reverse engineering algorithm.
#It returns a list of perturbed sentences, the attack set 
#This will request an exploitation budget from the user
def anchorPoints2(classifier, goal_classification, sentence_list, exploitation_budget):
    anchor_points = []
    search_radius = 1.0
    radius_min = .1
    radius_max = .5
    seed = sentence_list
    explore = seed
    count_legitimate = 0.0
    perturbed_sample = sentence_list[0]
    for i in range(1, exploration_budget + 1):
        exploreIndex = randint(0, len(explore) - 1)
        sample = explore[exploreIndex]
        search_radius = (radius_max - radius_min)*(count_legitimate/float(i)) + radius_min
        perturbed_sample = anchorPerturb(sample, search_radius)
        perturbed_vector = sentenceToVector(perturbed_sample)
        if(linear_classifier.get_classification(classifier, [perturbed_vector])[0] == goal_classification):
            explore = explore + [perturbed_sample]
            count_legitimate = count_legitimate + 1.0

    attack_set = []
    number_of_attacks = exploration_budget
    for i in range(1, number_of_attacks + 1):
        index1 = randint(0, len(explore) - 1)
        index2 = randint(0, len(explore) - 1)
        sample1 = explore[index1]
        sample2 = explore[index2]
        perturbed_sample1 = anchorPerturb(sample1, search_radius)
        perturbed_sample2 = anchorPerturb(sample2, search_radius)
        gamma = randint(0, 1)
        multiply1 = multiplySentence(perturbed_sample1, gamma)
        multiply2 = multiplySentence(perturbed_sample2, 1 - gamma)
        attack_set = attack_set + [addSentences(multiply1, multiply2)]
        
    return attack_set

#This makes a set of string labels matching label of num_labels size.
#It is used to create the labels for use in training the linear classifier.    
def makeLabels(num_labels, label):
    labels = [label]*num_labels
    return labels

#END REVERSE ENGINEERING SECTION	
	

#START SENTENCE COMPUTATION SECTION
#This section contains code for doing computations with the Word2Vec word vectors
#in sentences. 

#This does a multiplication of the sentence by a floating point value.
#It takes the sentence as a list of string words and a floating point value as input.
#The words in the sentence are converted one by one to word vectors.
#Then each feature in the vector is multiplied by the multiplier.
#Then the feature vector is converted back into a word.
#The sentence is returned as a list of string words.
def multiplySentence(sentence, multiplier):
    multiplied_sentence = sentence[:]
    for key, word in enumerate(sentence):
        if(word.lower() in model):
            temp = deepcopy(model[word.lower()])
            for feature in temp:
                feature = feature * multiplier
            new_word = model.similar_by_vector(temp, topn=1, restrict_vocab=None)
            multiplied_sentence[key] = new_word[0][0]
        else:
            print("Word " + word + " not in vocabulary") #Can't multiply a word that doesn't exist in the vocabulary
    return multiplied_sentence    

#this adds two word vectors together.  It takes two string words as input
#and returns a string word as output.
#Internally, it converts both words to vectors and then
#loops through and adds each pair of features
#before converting back to a string.
def addWords(word1, word2):
    temp1 = deepcopy(model[word1.lower()])
    temp2 = deepcopy(model[word2.lower()])
    temp3 = deepcopy(model[word1.lower()])
    for key, value in enumerate(temp1):
        temp3[key] = temp1[key] + temp2[key]
    return model.similar_by_vector(temp3, topn=1, restrict_vocab=None)
    
#This subtracts words, taking the first word - the second word.
#It takes string words as parameters and returns a string word.
#Internally, it converts the words to vectors, then loops through
#and subtracts each feature before converting back to a string. 
def subtractWords(word1, word2):
    temp1 = deepcopy(model[word1.lower()])
    temp2 = deepcopy(model[word2.lower()])
    temp3 = deepcopy(model[word1.lower()])
    for key, value in enumerate(temp1):
        temp3[key] = temp1[key] - temp2[key]
    return model.similar_by_vector(temp3, topn=1, restrict_vocab=None)

#This adds sentences.  It takes string sentences as input
#and returns string sentences as output.
#It loops through each pair of words in the sentences.
#If both words can be converted to vectors, it adds them using the
#addWords method.  If one word cannot be converted to a vector, it
#shows preference for the word that can be vectorized and uses that one.
#If neither can be a vector, it uses the word from the first sentence.
def addSentences(sentence1, sentence2):
    final_sentence = sentence1[:]    
    for key, word in enumerate(sentence1):
        if(word.lower() in model and sentence2[key].lower() in model):
            new_word = addWords(word.lower(), sentence2[key].lower())
            final_sentence[key] = new_word[0][0]
        elif(word.lower() in model): #if only one of the words is in the model, use that word.  This means we can better use perturbation
            final_sentence[key] = word.lower()
        elif(sentence2[key].lower() in model):
            final_sentence[key] = sentence2[key].lower()
        else:
            print("Word was not in vocabulary")#Can't add a word that doesn't exist in the vocabulary
    return final_sentence
   
#This subtracts sentences.  It takes string sentences as parameters
#and returns string sentences.  It loops through each pair of words.
#If both words can be converted to vectors, it subtracts them.
#If only one can be vectorized, it uses that word.
#If neither can be vectorized, it uses the word from the first sentence.  
def subtractSentences(sentence1, sentence2):
    final_sentence = sentence1[:]    
    for key, word in enumerate(sentence1):
        if(word.lower() in model and sentence2[key].lower() in model):
            new_word = subtractWords(word.lower(), sentence2[key].lower())
            final_sentence[key] = new_word[0][0]
        elif(word.lower() in model): #if only one of the words is in the model, use that word.  This means we can better use perturbation
            final_sentence[key] = word.lower()
        elif(sentence2[key].lower() in model):
            final_sentence[key] = sentence2[key].lower()
        else:
            print("Word was not in vocabulary")#Can't add a word that doesn't exist in the vocabulary
    return final_sentence
 
#this takes a string sentence as input and gives
#the output as one long vector (not divided into words) 
def sentenceToVector(sentence):
    vector = []
    for word in sentence:
        if(word.lower() in model):
            vector = vector + deepcopy(model[word.lower()]).tolist()
        else:
            vector = vector + ([0]*300)#TODO fix hardcoded 300
    return vector

#this takes a number of word features as input and returns a random
#string word by generating a random float for each feature in the word vector.    
def generateRandomWord(num_features):
    word_vector = []
    for i in range(0, num_features):
        word_vector = word_vector + [random.uniform(-1, 1)]
    word_vector = numpy.asarray(word_vector)
    word = model.similar_by_vector(word_vector, topn=1, restrict_vocab=None)
    return word[0][0]

#This generates a random sentence of a given length by generating
#the words one at a time.    
def generateRandomSentence(sentence_length, num_features_per_word):
    sentence = []
    for i in range(0, sentence_length):
        sentence = sentence + [generateRandomWord(num_features_per_word)]
    return sentence 

#This takes the inner product of two string words
#by first converting them to word vectors.
#return value is a floating point number.
def innerProductWords(word1, word2):
    product = 0
    vector1 = model[word1.lower()]
    vector2 = model[word1.lower()]
    for i in range(0, len(vector1) - 1):
        product = product + vector1[i] * vector2[i]
    return product

#This sums all features in a vector.  It takes a string word as input
#and returns a floating point number by converting the word to a vector then summing.     
def sumWordVector(word):
    sum = 0
    vector = model[word.lower()]
    for i in range(0, len(vector) - 1):
        sum = sum + vector[i]
    return sum

#this takes the inner product of a sentence by taking the inner product of each word
#and then summing them all together.  If both words can be vectorized,
#the inner product is taken.  If only one can be, its features are summed.
#If no word can be vectorized, nothing is added.    
def innerProductSentences(sentence1, sentence2):
    product = 0
    for key, word in enumerate(sentence1):
        if(word.lower() in model and sentence2[key].lower() in model):
            product = product + innerProductWords(word, sentence2[key])
        elif(word.lower() in model):
            product = product + sumWordVector(word)
        elif(sentence2[key].lower() in model):
            product = product + sumWordVector(sentence2[key])
        else:
            product = product
    return product
   
#This makes the sentences orthogonal using Gram-Schmidt process.
#I treat each sentence as one long vector and take the inner product of the entire thing,
#then divide and multiply.  The returned sentence is intended to be sentence 1 made orthogonal to
#sentence 2.  Input is two sets of strings (sentences) and output is a set of strings (sentence)
def makeOrthogonal(sentence1, sentence2):
    innerProduct1 = innerProductSentences(sentence1, sentence2)
    innerProduct2 = innerProductSentences(sentence2, sentence2)
    multiplier = innerProduct1 / innerProduct2
    orthogonal = multiplySentence(sentence2, multiplier)
    return orthogonal
	
#This method takes a string word as input and returns a floating point number.
#The number is the sum of all features in the word squared.	
def wordSumSquaredFeatures(word):
    total = 0
    temp = deepcopy(model[word.lower()])
    for feature in temp:
        total = total + math.pow(feature, 2)
    return total
 
#This takes a set of strings as input and returns a floating point number.
#It takes the norm of the sentence by treating it as one long vector.
#Norm is similar to Pythagorean theorem, but for a longer vector 
def sentenceNorm(sentence):
    total = 0
    for word in sentence:
        total = total + wordSumSquaredFeatures(word)    
    norm = math.sqrt(total)
    return norm

#This takes a list of string sentences, converts them to vectors, and returns them as a set of vectors.
#Sentences are treated as one long vector, not as sets of vectors.	
def sentenceListToVectors(sentence_list):
    vector_list = []
    sentence_vector = []
    for sentence in sentence_list:
        sentence_vector = []
        for word in sentence:
            if(word.lower() in model):
                sentence_vector = sentence_vector + deepcopy(model[word.lower()]).tolist()
            else:
                sentence_vector = sentence_vector + ([0]*300)#TODO fix hardcoded 300
        vector_list = vector_list + [sentence_vector]
    return vector_list

#This takes as input a word in its vector format, a list of indices for features to perturb in the word,
#and the distance to perturb them by.  It perturbs each feature in the vector by the given distance
#by adding it to each specified feature.  Then it returns the perturbed word in vector format.	
def perturb_features(word_vector, perturbed_feature_indexes, distance_to_perturb):
    for z in range(0, len(perturbed_feature_indexes)):
        perturbation = distance_to_perturb
        word_vector[perturbed_feature_indexes[z]] = word_vector[perturbed_feature_indexes[z]] + perturbation    
    return word_vector    

#This takes as input a string sentence list, the indices of words to perturb, the number of features to perturb,
#and the distance to perturb them by.  It returns a string sentence list that has been perturbed. 
#All selected words will be forced to perturb-- this method will continue running until the words at these
#indices have been perturbed (possible infinite loop may happen here) 
def perturb_words(sentence_list, perturbed_word_indexes, num_features_to_perturb, distance_to_perturb):
    perturbed_list = sentence_list[:]
    flag = False
    perturbed_feature_indexes = []
    for x in range(0, len(perturbed_word_indexes)):
        word = sentence_list[perturbed_word_indexes[x]]
        new_word = [['word', 1.0]]
        new_word[0][0] = word
        if(word.lower() in model):
            temp = deepcopy(model[word.lower()])
            while(word.lower() == new_word[0][0].lower()):
                perturbed_feature_indexes = choose_features_to_perturb(num_features_to_perturb, len(temp))
                temp = perturb_features(temp, perturbed_feature_indexes, distance_to_perturb)
                new_word = model.similar_by_vector(temp, topn=1, restrict_vocab=None)
            perturbed_list[perturbed_word_indexes[x]] = new_word[0][0]
        else:
            print("Word " + word + " not in vocabulary") #Can't perturb a word that doesn't exist in the vocabulary
    return perturbed_list	

#END SENTENCE COMPUTATION SECTION#	
	
	
#START OUTPUT HELPER SECTION#	
#This section contains methods that help with making output nice to look at.

#This takes a sentence list of words and a list of words to color in the sentence.
#It returns the same sentence list with the words at the specified indices
#surrounded with ANSI symbols to color them red.
def color_words_red(words_to_color, indices_to_color):
    colored_list = []
    temp = ''
    for key, value in enumerate(words_to_color):
        temp = value
        if key in indices_to_color:
            temp = '\x1b[31m' + value + '\x1b[37m'
        colored_list = colored_list + [temp]   
    return colored_list    

#This method takes two sentences as input.  It returns the second
#sentence with words colored red if they are different words from the
#same position in the first sentence.	
def makeChangedWordsRed(sentence1, sentence2):
    changed_indices = findChanged(sentence1, sentence2)
    new_sentence = color_words_red(sentence2, changed_indices)
    return new_sentence

#This loops through a sentence list to find a sentence that
#is not identical to the original sentence and return it.
#If it cannot find a sentence, it returns the original sentence.	
def findChangedSentence(sentence_list, original_sentence):
    perturbed_sentence = 0
    for key, word in enumerate(original_sentence):
        original_sentence[key] = word.lower()
    for sentence in reversed(sentence_list):
        if(sentence != original_sentence):
            perturbed_sentence = sentence
            break
    #If we don't find one, set it to the last member of the set.
    if(perturbed_sentence == 0):
        perturbed_sentence = perturbed_sentences[len(perturbed_sentences) - 1]
    return perturbed_sentence

#This method takes two sentences and compares each word.
#It returns a list of indices for words that are not identical.	
def findChanged(sentence1, sentence2):
    changedIndices = []
    for key, word in enumerate(sentence1):
        if(word.lower() != sentence2[key].lower()):
            changedIndices = changedIndices + [key]		
    return changedIndices
	
#END OUTPUT HELPER SECTION#


#MAIN METHOD SECTION#
#This is the main method.  It takes the user's initial sentence,
#gives menu options for the perturbation type, and outputs the perturbed sentence.    
if __name__ == '__main__':

    #model = Word2Vec.load("new_model")#"300features_40minwords_10context") #TODO this should not be hard coded
    
    #sentence = input("Please enter a sentence to perturb: ")
    with open('sentence.txt', 'r') as myfile:
        sentence=myfile.read().replace('\n', ' ')
    sentence = sentence.translate(str.maketrans('','',string.punctuation))
    original_sentence = sentence.split()
    if not original_sentence: #Word list is empty because it did not recognize the given input as words (example: all punctuation or all symbols outside of character set)
        print("Words could not be recognized")
        exit()
    perturbation_type = input("Please select a perturbation type.  1) Random, 2) Anchor Points 3) Reverse Engineering: ")
    perturbation_type = int(perturbation_type)
    perturbed_sentence = original_sentence
    if(perturbation_type == 1):
        num_words_to_perturb = input("Please enter a number of words to perturb: ")
        num_words_to_perturb = int(num_words_to_perturb)
        num_features_to_perturb = input("Please enter a number of features to perturb as a number between 1 and 300: ")
        num_features_to_perturb = int(num_features_to_perturb)
        #num_features_total = len(deepcopy(model[sentence_list[0].lower()]))
        if(num_features_to_perturb > num_features):
             num_features_to_perturb = num_features
        distance_to_perturb = input("Please enter the amount to perturb by in the vector space as a decimal between -1 and 1: ")
        distance_to_perturb = float(distance_to_perturb)
        perturbed_sentence = randomPerturbation(svm_classifier, original_sentence, num_words_to_perturb, num_features_to_perturb, distance_to_perturb)
    elif(perturbation_type == 2):
        exploration_budget = input("Please enter an integer exploration budget greater than 0: ")
        exploration_budget = int(exploration_budget)
        vector_sample = multiply_sentence(original_sentence)
        seed_classification = linear_classifier.get_classification(svm_classifier, [vector_sample])[0]		
        perturbed_sentences = anchorPoints(svm_classifier, seed_classification, [original_sentence], exploration_budget)
        perturbed_sentence = findChangedSentence(perturbed_sentences, original_sentence)		
        perturbed_sentence = makeChangedWordsRed(original_sentence, perturbed_sentence)
    elif(perturbation_type == 3):
        exploration_budget = input("Please enter an integer exploration budget greater than 0: ")
        exploration_budget = int(exploration_budget)   
        magnitude = input("Please enter floating point number greater than 0 for the magnitude: ")
        magnitude = float(magnitude)
        vector_sample = multiply_sentence(original_sentence)
        seed_classification = linear_classifier.get_classification(svm_classifier, [vector_sample])[0]
        classifier_and_sentences = reverseEngineeringExplore(svm_classifier, seed_classification, original_sentence, exploration_budget, magnitude)
        perturbed_sentences = classifier_and_sentences[1]
        classifier = classifier_and_sentences[0]
        exploitation_budget = input("Please enter an integer exploitation budget greater than 0: ")
        exploitation_budget = int(exploitation_budget)
        exploit = reverseEngineeringExploit(classifier, seed_classification, perturbed_sentences, exploitation_budget)
        #perturbed_sentence = perturbed_sentences[len(perturbed_sentences) - 1]
        perturbed_sentence = findChangedSentence(exploit, original_sentence)
		
        perturbed_sentence = makeChangedWordsRed(original_sentence, perturbed_sentence)
    else:
        print("Sentence was not perturbed because a valid perturbation type was not selected.  Valid entries are integers 1, 2, or 3")
   
    print("Original sentence: ")
    print(' '.join(original_sentence))
    
    print("Perturbed sentence: ")
    print(' '.join(perturbed_sentence))

#END MAIN METHOD SECTION#