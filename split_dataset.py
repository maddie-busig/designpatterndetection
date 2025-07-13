import pandas
import sys

combined_file = sys.argv[1]
train_file = sys.argv[2]
predict_file = sys.argv[3]

combined = pandas.read_csv(combined_file)
train = combined[combined['pattern'].notna()]
predict = combined[combined['pattern'].isna()]

train.to_csv(train_file)
predict.to_csv(predict_file)

