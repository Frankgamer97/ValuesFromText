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
    def __load_words(words, words_dict):
        test_words = [word.strip() for word in words]
        test_vectors_indexes = [words_dict[word] for word in test_words]
        return test_vectors_indexes


    @staticmethod
    def plot_haidt_embeddings(model: dict, data: dict):


        print("[PCA] Fitting model")

        words = list(model.keys())
        word_vectors = list(model.values())

        words_index = dict(zip(words, list(range(len(words)))))

        pca = PCA(n_components = 3, random_state=42)
        components = pca.fit_transform(word_vectors)

        traces = []

        print("[PCA] Building 3D embedding space")

        for haidt, words in data.items():
            indexes = Statistic.__load_words(words, words_index)
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
                width = 1500,
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