import numpy as np
import os
from sklearn.decomposition import PCA
from StorageHandler import StorageHandler

from gensim.scripts.glove2word2vec import glove2word2vec
from gensim.test.utils import datapath, get_tmpfile
from gensim.models import KeyedVectors
import plotly.graph_objs as go
import pickle


class Statistic:

    @staticmethod
    def __load_words(model, words, global_vectors):
        test_words = [word.strip() for word in words]
        test_vectors = np.array([model[w] for w in test_words])
        test_vectors_indexes = [np.where(global_vectors == vecna)[0][0] for vecna in test_vectors]

        return test_vectors_indexes

    @staticmethod
    def plot_haidt_embeddings(data: dict):

        model_name = os.path.join(StorageHandler.get_data_raw_dir(),"Glove","glove2word2vec_model.sav")
        model = None

        if not os.path.exists(model_name):
            print("[PCA] Building model")
            glove_file = os.path.join(StorageHandler.get_data_raw_dir(), "Glove","glove.6B.50d.txt")
            glove_file = datapath(glove_file)

            word2vec_glove_file = os.path.join(StorageHandler.get_data_raw_dir(), "Glove","glove.6B.50d.word2vec.txt")
            if not os.path.exists(word2vec_glove_file):
                word2vec_glove_file = get_tmpfile(word2vec_glove_file)

            glove2word2vec(glove_file, word2vec_glove_file)

            model = KeyedVectors.load_word2vec_format(word2vec_glove_file)
            pickle.dump(model, open(model_name, 'wb'))

        else:
            print("[PCA] Using cached model")
            model = pickle.load(open(model_name, 'rb'))

        print("[PCA] Fitting model")
        words = [ word for word in model.vocab ]
        word_vectors = np.array([model[w] for w in words])

        pca = PCA(random_state=42)
        components = pca.fit_transform(word_vectors)[:,:3]

        traces = []

        print("[PCA] Building 3D embedding space")

        for haidt, words in data.items():
            indexes = Statistic.__load_words(model, words, word_vectors)
            color = len(list(traces))

            trace = go.Scatter3d(
                x = components[indexes,0], 
                y = components[indexes,1],  
                z = components[indexes,2],
                text = words,
                name = haidt,
                textposition = "top center",
                textfont_size = 20,
                mode = 'markers+text',
                marker = {
                    'size': 10,
                    'opacity': 0.8,
                    'color': color
                }
            )

            traces.append(trace)

        layout = go.Layout(
                margin = {'l': 0, 'r': 0, 'b': 0, 't': 0},
                showlegend=True,
                legend=dict(
                x=1,
                y=0.5,
                font=dict(
                    family="Courier New",
                    size=25,
                    color="black"
                )),
                font = dict(
                    family = " Courier New ",
                    size = 15),
                autosize = False,
                width = 1000,
                height = 1000
                )

        plot_figure = go.Figure(data = traces, layout = layout)
        plot_figure.show()



if __name__ == "__main__":
    data = {
        'Harm': ['kill','fist','accident'],
        'Care': ['important','love','felling']
    }

    Statistic.plot_haidt_embeddings(data)