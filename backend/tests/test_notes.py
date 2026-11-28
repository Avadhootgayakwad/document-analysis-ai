from test_summaries import client


def create_note(client):

    response = client.post(
        "/api/notes/",
        json={
            "title": "Business Analysis",
            "content": "Important revenue findings.",
            "category": "Business",
            "tags": ["revenue", "analytics"]
        }
    )

    assert response.status_code == 201

    return response.json()


def test_create_note(client):

    note = create_note(client)

    assert note["source_type"] == "manual"


def test_generate_ai_note(client):

    response = client.post(
        "/api/notes/generate",
        json={
            "document_ids": client.document_ids,
            "title": "AI Business Notes",
            "category": "AI Insights"
        }
    )

    assert response.status_code == 201
    assert response.json()["source_type"] == "ai"


def test_list_notes(client):

    create_note(client)

    response = client.get("/api/notes/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_notes(client):

    create_note(client)

    response = client.get(
        "/api/notes/?search=revenue"
    )

    assert len(response.json()) == 1


def test_category_filter(client):

    create_note(client)

    response = client.get(
        "/api/notes/?category=Business"
    )

    assert len(response.json()) == 1


def test_tag_filter(client):

    create_note(client)

    response = client.get(
        "/api/notes/?tag=analytics"
    )

    assert len(response.json()) == 1


def test_categories(client):

    create_note(client)

    response = client.get(
        "/api/notes/categories"
    )

    assert "Business" in response.json()


def test_tags(client):

    create_note(client)

    response = client.get(
        "/api/notes/tags"
    )

    assert "analytics" in response.json()


def test_update_note(client):

    note = create_note(client)

    response = client.put(
        f"/api/notes/{note['id']}",
        json={
            "title": "Updated Analysis",
            "content": "Updated findings.",
            "category": "Business",
            "tags": ["updated"]
        }
    )

    assert response.status_code == 200

    assert response.json()["title"] == (
        "Updated Analysis"
    )


def test_export_note(client):

    note = create_note(client)

    response = client.get(
        f"/api/notes/{note['id']}/export"
    )

    assert response.status_code == 200
    assert response.json()["id"] == note["id"]


def test_delete_note(client):

    note = create_note(client)

    response = client.delete(
        f"/api/notes/{note['id']}"
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/notes/{note['id']}"
    )

    assert response.status_code == 404