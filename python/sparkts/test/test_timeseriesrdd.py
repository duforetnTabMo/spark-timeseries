from test_utils import PySparkTestCase
from timeseriesrdd import *
from datetimeindex import *
import pandas as pd
import numpy as np
from unittest import TestCase
from io import BytesIO

class TimeSeriesSerializerTestCase(TestCase):
    def test_times_series_serializer(self):
        serializer = TimeSeriesSerializer()
        stream = BytesIO()
        series = [('abc', np.array([4.0, 4.0, 5.0])), ('123', np.array([1.0, 2.0, 3.0]))]
        serializer.dump_stream(iter(series), stream)
        stream.seek(0)
        reconstituted = list(serializer.load_stream(stream))
        self.assertEquals(reconstituted[0][0], series[0][0])
        self.assertEquals(reconstituted[1][0], series[1][0])
        self.assertTrue((reconstituted[0][1] == series[0][1]).all())
        self.assertTrue((reconstituted[1][1] == series[1][1]).all())

class TimeSeriesRDDTestCase(PySparkTestCase):
    def test_time_series_rdd(self):
        freq = DayFrequency(1, self.sc)
        start = '2015-04-09'
        dt_index = uniform(start, 10, freq, self.sc)
        vecs = [np.arange(0, 10), np.arange(10, 20), np.arange(20, 30)]
        rdd = self.sc.parallelize(vecs).map(lambda x: (str(x[0]), x))
        tsrdd = TimeSeriesRDD(dt_index, rdd)
        self.assertEquals(tsrdd.count(), 3)

        contents = tsrdd.collectAsMap()
        self.assertEquals(len(contents), 3)
        self.assertTrue((contents["0"] == np.arange(0, 10)).all())
        self.assertTrue((contents["10"] == np.arange(10, 20)).all())
        self.assertTrue((contents["20"] == np.arange(20, 30)).all())

        subslice = tsrdd['2015-04-10':'2015-04-15']
        self.assertEquals(subslice.index(), uniform('2015-04-10', 6, freq, self.sc))
        contents = subslice.collectAsMap()
        self.assertEquals(len(contents), 3)
        self.assertTrue((contents["0"] == np.arange(1, 7)).all())
        self.assertTrue((contents["10"] == np.arange(11, 17)).all())
        self.assertTrue((contents["20"] == np.arange(21, 27)).all())

    def test_to_instants(self):
        # TODO: kryo registrator
        vecs = [np.arange(x, x + 4) for x in np.arange(0, 20, 4)]
        labels = ['a', 'b', 'c', 'd', 'e']
        start = '2015-4-9'
        dt_index = uniform(start, 4, DayFrequency(1, self.sc), self.sc)
        rdd = self.sc.parallelize(zip(labels, vecs), 3)
        tsrdd = TimeSeriesRDD(dt_index, rdd)
        samples = tsrdd.to_instants().collect()
        target_dates = ['2015-4-9', '2015-4-10', '2015-4-11', '2015-4-12']
        self.assertEquals([x[0] for x in samples], [pd.Timestamp(x) for x in target_dates])
        self.assertTrue((samples[0][1] == np.arange(0, 20, 4)).all())
        self.assertTrue((samples[1][1] == np.arange(1, 20, 4)).all())
        self.assertTrue((samples[2][1] == np.arange(2, 20, 4)).all())
        self.assertTrue((samples[3][1] == np.arange(3, 20, 4)).all())

