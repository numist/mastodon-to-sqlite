from copy import deepcopy

from mastodon_to_sqlite import service

from . import fixtures


def test_build_database(mock_db):
    service.build_database(mock_db)

    assert mock_db["accounts"].exists() is True
    assert mock_db["following"].exists() is True
    assert mock_db["statuses"].exists() is True


def test_transformer_account():
    account = fixtures.ACCOUNT_ONE.copy()

    service.transformer_account(account)

    assert account == {
        "id": fixtures.ACCOUNT_ONE["id"],
        "username": fixtures.ACCOUNT_ONE["username"],
        "url": fixtures.ACCOUNT_ONE["url"],
        "display_name": fixtures.ACCOUNT_ONE["display_name"],
        "note": fixtures.ACCOUNT_ONE["note"],
    }


def test_save_accounts(mock_db):
    account_one = fixtures.ACCOUNT_ONE.copy()
    account_two = fixtures.ACCOUNT_TWO.copy()

    service.save_accounts(mock_db, [account_one])

    assert mock_db["accounts"].count == 1
    assert mock_db["following"].count == 0

    service.save_accounts(
        mock_db,
        [account_two],
        followed_id=account_one["id"],
    )

    assert mock_db["accounts"].count == 2
    assert mock_db["following"].count == 1

    service.save_accounts(
        mock_db,
        [account_two],
        follower_id=account_one["id"],
    )

    assert mock_db["accounts"].count == 2
    assert mock_db["following"].count == 2


def test_transformer_status():
    status = deepcopy(fixtures.STATUS_ONE)

    service.transformer_status(status)

    assert status == {
        "id": fixtures.STATUS_ONE["id"],
        "created_at": fixtures.STATUS_ONE["created_at"],
        "content": fixtures.STATUS_ONE["content"],
        "account_id": fixtures.STATUS_ONE["account"]["id"],
        "reblog_of": None,
    }


def test_save_statuses(mock_db):
    status_reblog = deepcopy(fixtures.STATUS_REBLOG)
    status_two = deepcopy(fixtures.STATUS_TWO)

    service.save_statuses(mock_db, [status_reblog, status_two])

    assert mock_db["statuses"].exists() is True
    assert mock_db["statuses"].count == 3
    assert mock_db["accounts"].exists() is True
    assert mock_db["accounts"].count == 2


def test_save_activities(mock_db):
    status_one = deepcopy(fixtures.STATUS_ONE)
    status_two = deepcopy(fixtures.STATUS_TWO)

    service.save_activities(
        mock_db, "42", "bookmarked", [status_one, status_two]
    )

    assert mock_db["statuses"].exists() is True
    assert mock_db["statuses"].count == 2
    assert mock_db["status_activities"].exists() is True
    assert mock_db["status_activities"].count == 2
    for row in mock_db["status_activities"].rows:
        assert row["activity"] == "bookmarked"
        assert row["account_id"] == 42


def test_save_multiple_activity_types(mock_db):
    status_one = fixtures.STATUS_ONE
    status_two = fixtures.STATUS_TWO

    service.save_activities(
        mock_db,
        "42",
        "bookmarked",
        [deepcopy(status_one), deepcopy(status_two)],
    )
    service.save_activities(
        mock_db,
        "42",
        "favourited",
        [deepcopy(status_one), deepcopy(status_two)],
    )

    assert mock_db["statuses"].exists() is True
    assert mock_db["statuses"].count == 2
    assert mock_db["status_activities"].exists() is True
    assert mock_db["status_activities"].count == 4
    for row in mock_db["status_activities"].rows:
        assert row["account_id"] == 42


def test_extract_reblogs():
    status_noreblog = deepcopy(fixtures.STATUS_TWO)
    status_reblog = deepcopy(fixtures.STATUS_REBLOG)

    reblogs = service.extract_reblogs([status_reblog, status_noreblog])

    assert reblogs == [fixtures.STATUS_ONE]


# TODO: test media attachments
