import tempfile

from kkloader import KoikatuSaveData


def test_savedata_vanilla():
    tmpfile = tempfile.NamedTemporaryFile()
    ks = KoikatuSaveData.load("./data/kk_savedata.dat")
    ks.save(tmpfile.name)
    ks2 = KoikatuSaveData.load(tmpfile.name)
    assert bytes(ks) == bytes(ks2)
