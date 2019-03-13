import re
from collections import Counter
from datetime import datetime
import numpy as np
from Levenshtein import ratio, distance


jaro_thresh = 0.8
fingerprint_thresh = 2
lev_thresh = 0.9
n_gram = 3

lev_window = 25
lev_slide = 13

"""
Creates a matrix of potential matches for each entity in the database if distance is above threshold
"""

"""
    input: entities = [(entity, doc_id)]
"""
class Clustering:
    def __init__(self, algorithm, type):
        self.algorithm_mapping = {
            'levenshtein': self._get_lev_clusters,
            'fingerprint': self._fingerprint,
            'lev_slide': self._get_lev_clusters_slide
        }
        self.algorithm = algorithm
        self.cluster = self.algorithm_mapping[algorithm]
        self.type = type

        self.counts = {}
        self.all_entities = []
        self.cluster_by_name = {}
        self.cluster_lookup = {}
        self.clusters = []

    def get_clusters(self, entities):
        # drop duplicates and get entity counts
        #all_entities = [x[0] for x in list(set(entities))]

        self.obj_map = {}
        self.counts = Counter()

        for obj, count in entities:
            alias = count[0]
            count = count[1]
            self.counts[alias] += count

            if alias not in self.obj_map:
                self.obj_map[alias] = []

            self.obj_map[alias] += [obj]

        self.all_entities = sorted(self.counts.keys())

        # TODO: remove
        t1 = datetime.now()
        self.cluster()
        self._reduce()
        print(datetime.now() - t1)

        return self._get_cluster_objs()

    def _get_lev_clusters_slide(self):
        for i in range(0, len(self.all_entities), lev_slide):
            window = self.all_entities[i + 1:i + lev_window]
            self._get_lev_clusters(window)

        # reverse each word and sort
        reversed = sorted([x[::-1] for x in self.all_entities])
        for i in range(0, len(reversed), lev_slide):
            window = reversed[i + 1:i + lev_window]
            self._get_lev_clusters(window, reversed=True)

        return

    def _get_lev_clusters(self, words, reversed=False):
        num = len(words)

        for i in range(num):
            word = words[i]
            cluster = [x for x in words[i + 1:] if self._ngam_match(word.lower(), x.lower(), n_gram)
                       and ratio(word.lower(), x.lower()) >= lev_thresh]
            if len(cluster) > 0:
                cluster += [word]
                # On reverse pass, only add cluster if > 2
                if reversed:
                    if len(cluster) > 2:
                        cluster = [x[::-1] for x in cluster]
                    else:
                        continue
                self._insert_cluster_lookup(cluster)

        return

    def _insert_cluster_lookup(self, cluster):
        for member in cluster.copy():
            if member in self.cluster_by_name:
                # get the cluster associated with member
                subcluster = self.cluster_by_name[member]
                cluster += subcluster

                # remove subcluster from cluster_lookup
                self.cluster_lookup.pop(tuple(subcluster), None)

        cluster = list(set(cluster))
        for member in cluster:
            self.cluster_by_name[member] = cluster

        self.cluster_lookup[tuple(cluster)] = None

        return

    def _get_top_entities(self, words, length=1000):
        all_words = [x[0] for x in words]

        # Remove duplicates and Count, faster processing here than SQL
        counts = Counter([x[0] for x in list(dict.fromkeys(words))])
        top_entities = [x[0] for x in counts.most_common(1000)]
        return top_entities

    def _get_cluster_count(self, cluster):
        count = 0
        for word in cluster:
            count += self.counts[word]

        return count

    """
        TODO: classify strings that have more than 1 word, this usually indicates full names
    """
    def _fingerprint(self, words, counts):
        pattern = re.compile('[\W_]+')

        def _clean_sort(word):
            clean = pattern.sub(' ', word.lower())
            clean = clean.split(' ')
            clean.sort()
            return ' '.join(clean).strip()

        fingerprints = [_clean_sort(x) for x in words]
        duplicates = [x[0] for x in Counter(fingerprints).items() if x[1] >= fingerprint_thresh]

        clusters = [[] for x in range(len(duplicates))]

        for idx, fingerprint in enumerate(fingerprints):
            try:
                cluster_idx = duplicates.index(fingerprint)
                clusters[cluster_idx].append(words[idx])
            # Not a duplicate
            except ValueError as err:
                continue

        # Return clusters and there counts
        return [(x, self._reduce(x, counts)) for x in clusters]

    def _ngam_match(self, word1, word2, n=3):
        if len(word1) < n or len(word2) < n:
            return False

        word1 = word1.lower()
        word2 = word2.lower()

        for i in range(len(word1)):
            if word1[i:i+n] in word2:
                return True

        return False

    def _reduce(self):
        for cluster in self.cluster_lookup:
            self.clusters.append((list(cluster), self._get_cluster_count(cluster)))
        return

    def _get_cluster_objs(self):
        clusters = []
        for cluster in self.clusters:
            objs = []
            group = cluster[0]
            count = cluster[1]
            for name in group:
                objs += self.obj_map[name]
            clusters.append({
                'entities': objs,
                'count': count,
                'algorithm': self.algorithm,
                'type': self.type,
                'status': 'PENDING'
            })
        return clusters
