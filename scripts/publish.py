#!/usr/bin/env python3
"""Publishes a library's shelves to Little Keebo's downloads host.

The same file is library/scripts/publish.py in dreamforces/little-keebo and scripts/publish.py in
dreamforces/little-keebo-community; the library's check fails when the two differ.

    publish.py --source library --account <storage account> --key-id <Key Vault key id>
    publish.py --source library --out <folder> --sign-pem <private key.pem>      (a dry run, signed with a local key)

Run in the library's root (the folder holding extensions/, phrases/ and templates/, each with the index.json that
build-extension-index.py writes). For each shelf:

1. Every package goes up once per version to extensions/<source>/<shelf>/<id>/<version>/<file>, create-only. A version
   already published must have the same bytes; if it does not, its version was not bumped and nothing more is published.
2. The shelf's index is rebuilt with those paths and signed: ECDSA P-256 over its SHA-256, by the library's key in Key Vault
   (az keyvault key sign --algorithm ES256). The signature is checked against the key's public half with openssl before
   anything is uploaded.
3. feeds/<source>/<shelf>/index.json is written last: the index's bytes (base64), the key's name and the signature, in one
   file, so a reader never pairs an index with another one's signature. The app checks it with the keys built into it.

Needs the az CLI (signed in, as the release workflow is) and openssl. Uses only the standard library.
"""
import argparse, base64, datetime, hashlib, json, os, pathlib, subprocess, sys, tempfile

SHELVES = ("extensions", "phrases", "templates")
TYPES = {".json": "application/json", ".js": "text/javascript"}


def run(*args, check=True):
    done = subprocess.run(args, capture_output=True, text=True)
    if check and done.returncode != 0:
        sys.exit(f"error: {' '.join(args[:4])}…: {done.stderr.strip() or done.stdout.strip()}")
    return done


def der_from_raw(raw):
    """A 64-byte r‖s signature as DER, which openssl reads."""
    def integer(b):
        b = b.lstrip(b"\x00") or b"\x00"
        if b[0] & 0x80: b = b"\x00" + b
        return b"\x02" + bytes([len(b)]) + b
    body = integer(raw[:32]) + integer(raw[32:])
    return b"\x30" + bytes([len(body)]) + body


def b64decode_any(text):
    text = text.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(text + "=" * (-len(text) % 4))


class Host:
    """The storage account, through az (signed in), or a folder for a dry run."""

    def __init__(self, account=None, out=None):
        self.account, self.out = account, pathlib.Path(out) if out else None

    def existing(self, container, name):
        """The blob's bytes, or None when it is not there."""
        if self.out:
            path = self.out / container / name
            return path.read_bytes() if path.exists() else None
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "blob")
            done = run("az", "storage", "blob", "download", "--auth-mode", "login", "--account-name", self.account,
                       "--container-name", container, "--name", name, "--file", target, "--no-progress", "--only-show-errors", check=False)
            if done.returncode != 0:
                if "BlobNotFound" in done.stderr or "does not exist" in done.stderr or "ErrorCode:BlobNotFound" in done.stdout:
                    return None
                sys.exit(f"error: reading {container}/{name}: {done.stderr.strip()}")
            return pathlib.Path(target).read_bytes()

    def put(self, container, name, data, content_type, overwrite, cache=None):
        if self.out:
            path = self.out / container / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return
        with tempfile.TemporaryDirectory() as folder:
            source = os.path.join(folder, "blob")
            pathlib.Path(source).write_bytes(data)
            # One Put Blob: the release identity may create blobs but not write blocks (infra/README.md).
            args = ["az", "storage", "blob", "upload", "--auth-mode", "login", "--account-name", self.account, "--container-name", container,
                    "--name", name, "--file", source, "--content-type", content_type, "--overwrite", "true" if overwrite else "false",
                    "--no-progress", "--only-show-errors"]
            if cache: args += ["--content-cache-control", cache]
            run(*args)


class Signer:
    """Key Vault's key, through az, or a local private key for a dry run. Both are checked with openssl against `public_pem`."""

    def __init__(self, key_id=None, pem=None):
        self.key_id, self.pem = key_id, pem
        with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as handle:
            self.public_pem = handle.name
        if pem:
            run("openssl", "pkey", "-in", pem, "-pubout", "-out", self.public_pem)
        else:
            assert key_id, "a key id or a local key is needed"
            vault = key_id.split("//")[1].split(".")[0]
            name = key_id.rstrip("/").split("/keys/")[1].split("/")[0]
            pathlib.Path(self.public_pem).unlink()
            run("az", "keyvault", "key", "download", "--vault-name", vault, "--name", name, "--encoding", "PEM", "--file", self.public_pem)

    def sign(self, data):
        """The signature of `data` as Key Vault gives it: 64 raw bytes (r‖s), base64url."""
        digest = hashlib.sha256(data).digest()
        if self.pem:
            with tempfile.TemporaryDirectory() as folder:
                pathlib.Path(folder, "digest").write_bytes(digest)
                run("openssl", "pkeyutl", "-sign", "-inkey", self.pem, "-in", os.path.join(folder, "digest"), "-out", os.path.join(folder, "sig"))
                der = pathlib.Path(folder, "sig").read_bytes()
            raw = raw_from_der(der)
            signature = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        else:
            assert self.key_id
            done = run("az", "keyvault", "key", "sign", "--id", self.key_id, "--algorithm", "ES256",
                       "--digest", base64.b64encode(digest).decode(), "-o", "json")
            signature = json.loads(done.stdout)["signature"]
        self.check(digest, signature)
        return signature

    def check(self, digest, signature):
        raw = b64decode_any(signature)
        if len(raw) != 64:
            sys.exit(f"error: the signature is {len(raw)} bytes, not the 64 the app reads")
        with tempfile.TemporaryDirectory() as folder:
            pathlib.Path(folder, "digest").write_bytes(digest)
            pathlib.Path(folder, "sig").write_bytes(der_from_raw(raw))
            done = run("openssl", "pkeyutl", "-verify", "-pubin", "-inkey", self.public_pem, "-in", os.path.join(folder, "digest"),
                       "-sigfile", os.path.join(folder, "sig"), check=False)
            if done.returncode != 0:
                sys.exit("error: the index's signature does not verify with the key's public half; nothing was published")


def raw_from_der(der):
    """r‖s from a DER ECDSA signature."""
    def integer(at):
        assert der[at] == 0x02
        length = der[at + 1]
        value = der[at + 2:at + 2 + length].lstrip(b"\x00")
        return value.rjust(32, b"\x00"), at + 2 + length
    assert der[0] == 0x30
    r, at = integer(2)
    s, _ = integer(at)
    return r + s


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", choices=("library", "community"), required=True)
    parser.add_argument("--account", help="storage account (DOWNLOADS_STORAGE_ACCOUNT)")
    parser.add_argument("--key-id", help="Key Vault key id (SHELF_SIGNING_KEY_ID)")
    parser.add_argument("--out", help="dry run: write what would be published into this folder")
    parser.add_argument("--sign-pem", help="dry run: sign with this local private key instead of Key Vault")
    args = parser.parse_args()
    if args.out:
        if not args.sign_pem: sys.exit("error: a dry run (--out) signs with --sign-pem")
    elif not (args.account and args.key_id):
        sys.exit("error: --account and --key-id are needed to publish")

    host = Host(args.account, args.out)
    signer = Signer(args.key_id, args.sign_pem)
    key_name = (args.key_id or "").rstrip("/").split("/keys/")[-1].split("/")[0] or f"shelf-{args.source}"
    published = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    feeds = []
    for shelf in SHELVES:
        listing = pathlib.Path(shelf, "index.json")
        if not listing.exists():
            continue
        packages = []
        for entry in json.loads(listing.read_text())["packages"]:
            local = pathlib.Path(entry["path"])
            data = local.read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                sys.exit(f"error: {local} does not match its index; run scripts/build-extension-index.py")
            name = f"{args.source}/{shelf}/{entry['id']}/{entry['version']}/{local.name}"
            there = host.existing("extensions", name)
            if there is None:
                host.put("extensions", name, data, TYPES[local.suffix], overwrite=False)
                print(f"uploaded extensions/{name}")
            elif there != data:
                sys.exit(f"error: {entry['id']} {entry['version']} is already published with other contents; bump its version")
            packages.append({**entry, "path": f"extensions/{name}"})
        index = {"schemaVersion": 2, "source": args.source, "shelf": shelf, "published": published, "packages": packages}
        data = (json.dumps(index, indent=2, ensure_ascii=False) + "\n").encode()
        envelope = {"schemaVersion": 2, "key": key_name, "index": base64.b64encode(data).decode(), "signature": signer.sign(data)}
        feeds.append((f"{args.source}/{shelf}/index.json", (json.dumps(envelope, indent=2) + "\n").encode(), len(packages)))
    # The feeds go last, once every package they list is up.
    for name, data, count in feeds:
        host.put("feeds", name, data, "application/json", overwrite=True, cache="public, max-age=300")
        print(f"published feeds/{name}: {count} package(s)")


if __name__ == "__main__":
    main()
