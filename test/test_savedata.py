import tempfile

from kkloader import KoikatuSaveData, SummerVacationSaveData


def test_savedata_vanilla():
    tmpfile = tempfile.NamedTemporaryFile()
    ks = KoikatuSaveData.load("./data/kk_savedata.dat")
    ks.save(tmpfile.name)
    ks2 = KoikatuSaveData.load(tmpfile.name)
    assert bytes(ks) == bytes(ks2)


def test_summervacation_savedata():
    tmpfile = tempfile.NamedTemporaryFile()
    svsd = SummerVacationSaveData.load("./data/sv_savedata.dat")
    svsd.save(tmpfile.name)
    svsd2 = SummerVacationSaveData.load(tmpfile.name)
    assert svsd.meta["WorldName"] == svsd2.meta["WorldName"]
    assert len(svsd.charas) == len(svsd.chara_details) == len(svsd2.charas) == len(svsd2.chara_details)
    assert bytes(svsd) == bytes(svsd2)
