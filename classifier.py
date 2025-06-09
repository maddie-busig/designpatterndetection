import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_fscore_support
from sklearn.linear_model import RandomizedLogisticRegression, LogisticRegression, RidgeClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier,VotingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import cross_val_score
import sys
# import pprint		# Used for pretty printing dictionaries
import random
import re

# initialization of the RNG
np.random.seed(2016)

if len(sys.argv)==2:
    algorithm = sys.argv[1]
else:
    algorithm = "RF"

assert algorithm in ["RF","SVM","GBTREE","ADABOOST","ADABOOST_LOGISTIC","LOGISTIC","RIDGE","VOTER", "EXTRA_TREES"]
print "Algorithm Used = %s"%(algorithm)

# Filename of the dataset
#data_file = "dataset.csv"
data_file = "P-MARt-dataset.csv"

# Read data from a csv file into a pandas dataframe
data = pd.read_csv(data_file)
data["implements"] = data["implements"].fillna(False)
# Rename the columns containing text
print(data.pattern.value_counts())
sys.stdout.flush()

# Lets keep classes which have atleast 10 value counts, otherwise model cant learn
vc = data.pattern.value_counts()
vc = vc[vc>=10]
labels_keep = set(vc.index)
print("Shape before filtering of data: ",data.shape)
data = data[data.pattern.isin(labels_keep)]
data = data.sample(frac=1)
print("Shape after filtering of data: ",data.shape)

# Label Encoding: Design patterns (text) to ordinal labels (numeric)
le = LabelEncoder()
data.pattern = le.fit_transform(data.pattern)	# Encode the labels/patterns
# Construct lookup table for quick reference without using the le object
label_lookup = le.classes_

# strip the project, class name and design pattern label
y = data['pattern']					# Labels (y)
X = data.drop(['pattern','project_name','class_name',
			   'class_implements_last_name','class_last_name','class_last_name_is_different',
			   'implements_name'], axis=1)	# Keep only feature columns for independent vars (x)
X.fillna(0,inplace=True)

# ====K-FOLD STRATIFIED CROSS VALIDATION=====

def train_test_get_metrics(model_builder,X_train, X_test, y_train, y_test):
    model = model_builder()
    model.fit(X_train, y_train) #.astype(float)
    y_pred = model.predict(X_test)
    cm = confusion_matrix(label_lookup[y_test], label_lookup[y_pred], label_lookup)
    accuracy = np.trace(cm) / float(np.sum(cm))
    misclassification = 1 - accuracy
    precision, recall, fscore, support = precision_recall_fscore_support(label_lookup[y_test], label_lookup[y_pred])
    precision_final, recall_final, fscore_final, _ = precision_recall_fscore_support(label_lookup[y_test],
                                                                                     label_lookup[y_pred],
                                                                                     average='macro')
    balanced_accuracy = balanced_accuracy_score(label_lookup[y_test], label_lookup[y_pred])
    return cm,accuracy,balanced_accuracy,misclassification,precision,recall,fscore,support,precision_final, recall_final, fscore_final


def random_forest():
    return RandomForestClassifier(n_estimators=1000)

def gb_tree():
    return GradientBoostingClassifier(n_estimators=100,max_depth=8,subsample=0.7,min_samples_leaf=4)

def adaboost_tree():
    return AdaBoostClassifier(base_estimator=RandomForestClassifier(n_estimators=100),n_estimators=20) # removed learning rate = 0.5
    
def adaboost_logistic():
    return AdaBoostClassifier(base_estimator=LogisticRegression(solver='lbfgs',class_weight="balanced",penalty="l2",multi_class="auto",n_jobs=-1,max_iter=500),
                              n_estimators=10,learning_rate=0.5)

def logistic():
    return make_pipeline(StandardScaler(),LogisticRegression(solver='saga',class_weight="balanced",penalty="l1",multi_class="auto",n_jobs=-1))

def ridge():
    return RidgeClassifier(alpha=0.3,normalize=True,class_weight="balanced")

def svm():
    return make_pipeline(StandardScaler(),SVC(class_weight="balanced",gamma='scale',C=1000.0,kernel="rbf",max_iter=100000,probability=True))

def voter():
    return VotingClassifier(estimators=[("svm",svm()),("rf",random_forest()),("adaboost",adaboost_tree())],
                            voting="soft")

def extra_trees():
    return ExtraTreesClassifier(bootstrap=False, criterion="gini", max_features=0.35000000000000003, min_samples_leaf=11, min_samples_split=15, n_estimators=100)


if algorithm=="RF":
    model_builder = random_forest
elif algorithm=="GBTREE":
    model_builder = gb_tree
elif algorithm=="ADABOOST":
    model_builder = adaboost_tree
elif algorithm=="ADABOOST_LOGISTIC":
    model_builder = adaboost_logistic
elif algorithm=="LOGISTIC":
    model_builder = logistic
elif algorithm=="RIDGE":
    model_builder = ridge
elif algorithm=="SVM":
    model_builder = svm
elif algorithm=="VOTER":
    model_builder = voter
elif algorithm=="EXTRA_TREES":
    model_builder = extra_trees


skf = StratifiedKFold(n_splits=10)
cv_results = []
for train_index, test_index in skf.split(X, y):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    r = train_test_get_metrics(model_builder,X_train, X_test, y_train, y_test)
    cv_results.append(r)

def summarise_cv_results(cv_results):
    cm, accuracy, balanced_accuracy, misclassification, precision, recall, fscore,support, precision_final, recall_final, fscore_final = list(),list(),list(),list(),list(),list(),list(),list(),list(),list(),list()
    for r in cv_results:
        cm.append(r[0])
        accuracy.append(r[1])
        balanced_accuracy.append(r[2])
        misclassification.append(r[3])
        precision.append(r[4])
        recall.append(r[5])
        fscore.append(r[6])
        support.append(r[7])
        precision_final.append(r[8])
        recall_final.append(r[9])
        fscore_final.append(r[10])


    accuracy = np.mean(accuracy)
    balanced_accuracy = np.mean(balanced_accuracy)
    misclassification = np.mean(misclassification)

    precision_final = np.mean(precision_final)
    recall_final = np.mean(recall_final)
    fscore_final = np.mean(fscore_final)

    precision = np.mean(precision,axis=0)
    recall = np.mean(recall,axis=0)
    fscore = np.mean(fscore,axis=0)
    support = np.mean(support,axis=0).astype(int)
    #cm = np.mean(cm,axis=0).astype(int)# mean not required
    cm = np.sum(cm,axis=0).astype(int)

    return cm, accuracy, balanced_accuracy, misclassification, precision, recall, fscore, support, precision_final, recall_final, fscore_final

cm, accuracy, balanced_accuracy, misclassification, precision, recall, fscore, support, precision_final, recall_final, fscore_final = summarise_cv_results(cv_results)

# Save the confusion matrix to file
with open("results/confusion_matrix_%s.csv"%(algorithm), "w") as f:
	ordered_patterns = []
	for i in range(len(cm[0])):
		ordered_patterns.append(label_lookup[i])
	f.write("{0}\n".format(",".join(ordered_patterns)))
	for row in cm:
		f.write("{0}\n".format(",".join([str(i) for i in row])))

classification_report_df = pd.DataFrame({"labels":label_lookup,"precision":precision,"recall":recall,"fscore":fscore,"support":support})
classification_report_df.to_csv("results/evaluation_%s.csv"%(algorithm),index=False)

