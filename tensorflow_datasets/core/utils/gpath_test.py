"""Tests for tensorflow_datasets.core.utils.gpath."""

import os
import pathlib

import pytest
import tensorflow as tf
from pathlib import Path
from tensorflow_datasets import testing
from tensorflow_datasets.core.utils.gpath import GcsPath


@pytest.fixture
def mocked_gfile_path(tmp_path: pathlib.Path):
  def _norm_path(path: str):
    return path.replace('gs://', os.fspath(tmp_path) + '/')

  with testing.mock_tf(
      'tf.io.gfile',
      exists=lambda p: os.path.exists(_norm_path(p)),
      isdir=lambda p: os.path.isdir(_norm_path(p)),
      listdir=lambda p: os.listdir(_norm_path(p)),
      GFile=lambda p, *args, **kwargs: open(_norm_path(p), *args, **kwargs),
      rename=lambda p1, p2: os.rename(_norm_path(p1), _norm_path(p2)),
      replace=lambda p1, p2, **kwargs: os.replace(_norm_path(p1), _norm_path(p2), **kwargs),
      mkdir=lambda p: os.mkdir(_norm_path(p)),
      makedirs=lambda p: os.makedirs(_norm_path(p)),
      glob=lambda p: Path(_norm_path(p)).parent.glob(Path(_norm_path(p)).stem)  # TODO: temporary func
  ):
    yield tmp_path


def test_gfs(mocked_gfile_path: pathlib.Path):
  g_path = GcsPath('gs://bucket/dir')
  assert not g_path.exists()

  # mkdir()
  g_path.mkdir(parents=True)

  # exists()
  assert g_path.exists()
  assert mocked_gfile_path.joinpath('bucket/dir').exists()

  # is_dir()
  assert not mocked_gfile_path.joinpath('read_text_file.txt').is_dir()
  assert g_path.is_dir()


def test_functions(mocked_gfile_path: pathlib.Path):

  files = ['foo.py', 'bar.py', 'foo_bar.py', 'dataset.json',
           'dataset_info.json', 'readme.md']
  dataset_path = GcsPath('gs://bucket/dataset')

  dataset_path.mkdir(parents=True)
  assert dataset_path.exists()

  # open()
  for file in files:
    with dataset_path.joinpath(file).open('w') as f:
      f.write(' ')

  # iterdir()
  assert len(list(mocked_gfile_path.joinpath('bucket/dataset').iterdir())) == 6


def test_read_write(mocked_gfile_path: pathlib.Path):
  # read_text()
  with tf.io.gfile.GFile('gs://text_file.txt', 'w') as f:
    f.write('abcd')
  assert mocked_gfile_path.joinpath('text_file.txt').read_text() == 'abcd'

  # read_bytes()
  with tf.io.gfile.GFile('gs://bytes_file.txt', 'wb') as f:
    f.write(b'abcd')
  assert mocked_gfile_path.joinpath('bytes_file.txt').read_bytes() == b'abcd'

  write_file_path = GcsPath('gs://text_file1.txt')
  write_bytes_path = GcsPath('gs://bytes_file1.txt')

  # write_text() write_bytes()
  write_file_path.write_text('abcd')
  write_bytes_path.write_bytes(b'foobar')

  # read_text() read_bytes()
  assert mocked_gfile_path.joinpath('text_file1.txt').read_text() == 'abcd'
  assert mocked_gfile_path.joinpath('bytes_file1.txt').read_bytes() == b'foobar'


def test_mkdir(mocked_gfile_path: pathlib.Path):
  g_path = GcsPath('gs://bucket')
  assert not g_path.exists()

  g_path.mkdir()
  assert g_path.exists()
  assert mocked_gfile_path.joinpath('bucket').exists()


def test_rename_replace(mocked_gfile_path: pathlib.Path):
  src_path = GcsPath('gs://foo.py')
  src_path.write_text(' ')

  assert mocked_gfile_path.joinpath('foo.py').exists()

  # Rename()
  # target_path = GcsPath('gs://foo.py')
  src_path.rename('gs://bar.py')
  # target = GcsPath(mocked_gfile_path.joinpath())
  # GcsPath(mocked_gfile_path.joinpath('foo.py')).rename('bar.py')

  assert not mocked_gfile_path.joinpath('foo.py').exists()
  assert mocked_gfile_path.joinpath('bar.py').exists()
