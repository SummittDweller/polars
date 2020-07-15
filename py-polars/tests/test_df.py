from polars import DataFrame, Series
import pytest


def test_init():
    df = DataFrame({"a": [1, 2, 3], "b": [1.0, 2.0, 3.0]})

    # length mismatch
    with pytest.raises(RuntimeError):
        df = DataFrame({"a": [1, 2, 3], "b": [1.0, 2.0, 3.0, 4.0]})


def test_selection():
    df = DataFrame({"a": [1, 2, 3], "b": [1.0, 2.0, 3.0], "c": ["a", "b", "c"]})

    assert df["a"].dtype == "i64"
    assert df["b"].dtype == "f64"
    assert df["c"].dtype == "str"

    assert df[["a", "b"]].columns == ["a", "b"]
    assert df[[True, False, True]].height == 2

    assert df[[True, False, True], "b"].shape == (2, 1)
    assert df[[True, False, False], ["a", "b"]].shape == (1, 2)

    assert df[[0, 1], "b"].shape == (2, 1)
    assert df[[2], ["a", "b"]].shape == (1, 2)


def test_sort():
    df = DataFrame({"a": [2, 1, 3], "b": [1, 2, 3]})
    df.sort("a", in_place=True)
    assert df.frame_equal(DataFrame({"a": [1, 2, 3], "b": [2, 1, 3]}))


def test_replace():
    df = DataFrame({"a": [2, 1, 3], "b": [1, 2, 3]})
    s = Series("c", [True, False, True])
    df.replace("a", s)
    assert df.frame_equal(DataFrame({"c": [True, False, True], "b": [1, 2, 3]}))


def test_slice():
    df = DataFrame({"a": [2, 1, 3], "b": ["a", "b", "c"]})
    df = df.slice(1, 2)
    assert df.frame_equal(DataFrame({"a": [1, 3], "b": ["b", "c"]}))


def test_head_tail():
    df = DataFrame({"a": range(10), "b": range(10)})
    assert df.head(5).height == 5
    assert df.tail(5).height == 5

    assert not df.head(5).frame_equal(df.tail(5))
    # check if it doesn't fail when out of bounds
    assert df.head(100).height == 10
    assert df.tail(100).height == 10


def test_groupby():
    df = DataFrame(
        {
            "a": ["a", "b", "a", "b", "b", "c"],
            "b": [1, 2, 3, 4, 5, 6],
            "c": [6, 5, 4, 3, 2, 1],
        }
    )
    assert df.groupby(by="a", select="b", agg="sum").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [4, 11, 6]})
    )
    assert df.groupby(by="a", select="c", agg="sum").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [10, 10, 1]})
    )
    assert df.groupby(by="a", select="b", agg="min").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [1, 2, 6]})
    )
    assert df.groupby(by="a", select="b", agg="min").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [1, 2, 6]})
    )
    assert df.groupby(by="a", select="b", agg="max").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [3, 5, 6]})
    )
    assert df.groupby(by="a", select="b", agg="mean").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [2.0, (2 + 4 + 5) / 3, 6.0]})
    )

    # TODO: is false because count is u32
    df.groupby(by="a", select="b", agg="count").frame_equal(
        DataFrame({"a": ["a", "b", "c"], "": [2, 3, 1]})
    )


def test_join():
    df_left = DataFrame(
        {"a": ["a", "b", "a", "z"], "b": [1, 2, 3, 4], "c": [6, 5, 4, 3],}
    )
    df_right = DataFrame(
        {"a": ["b", "c", "b", "a"], "k": [0, 3, 9, 6], "c": [1, 0, 2, 1],}
    )

    joined = df_left.join(df_right, left_on="a", right_on="a").sort("a")
    assert joined["b"].series_equal(Series("", [1, 3, 2, 2]))
    joined = df_left.join(df_right, left_on="a", right_on="a", how="left").sort("a")
    assert joined["c_right"].is_null().sum() == 1
    assert joined["b"].series_equal(Series("", [1, 3, 2, 2, 4]))
    joined = df_left.join(df_right, left_on="a", right_on="a", how="outer").sort("a")
    assert joined["c_right"].null_count() == 1
    assert joined["c"].null_count() == 2
    assert joined["b"].null_count() == 2
