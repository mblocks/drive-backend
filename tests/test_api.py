# -*- coding: utf-8 -*-

from typing import List


current_user = {
    'x-consumer-id': '1',
    'x-consumer-third': 'mblocks',
    'x-consumer-third-user-id': '1',
    'x-consumer-third-user-name': 'lizhixin'
}


def test_dirs_post(client):
    response = client.post(
        '/dirs',
        headers=current_user,
        json={
            "name": "string"
        }
    )
    assert response.status_code == 200


def test_dirs_get(client):
    response = client.get(
        '/dirs',
        headers=current_user,
    )
    assert response.status_code == 200


def test_presigned_get(client):
    response = client.get(
        '/presigned',
        headers=current_user,
    )
    data = response.json()
    assert response.status_code == 200
    assert 'policy' in data


def test_breadcrumb_get(client):
    response = client.get(
        '/breadcrumb',
        headers=current_user,
    )
    data = response.json()
    assert response.status_code == 200
    assert type(data) == list


def test_documents_get(client):
    response = client.get(
        '/documents',
        headers=current_user,
    )
    data = response.json()
    assert response.status_code == 200
    assert type(data) == list


def test_documents_move(client):
    response = client.post(
        '/documents/move',
        headers=current_user,
        json={
            'target': 2,
            'documents': [
                3
            ]
        }
    )
    assert response.status_code == 200


def test_documents_copy(client):
    response = client.post(
        '/documents/copy',
        headers=current_user,
        json={
            'target': 2,
            'documents': [
                3
            ]
        }
    )
    assert response.status_code == 200


def test_documentsupdate(client):
    response = client.post(
        '/documents/update',
        headers=current_user,
        json={
            "id": 4,
            "name": "newstring"
        }
    )
    assert response.status_code == 200


def test_documents_delete(client):
    response = client.post(
        '/documents/delete',
        headers=current_user,
        json=[4]
    )
    assert response.status_code == 200


def test_documents_download(client):
    response = client.get(
        '/documents/download?id=3',
        headers=current_user
    )
    assert response.status_code == 200
