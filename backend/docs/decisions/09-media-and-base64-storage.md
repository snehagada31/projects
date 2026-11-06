# Decision Record 09: Media and Base64 Avatar Storage Architecture

**Decision:**
Store profile avatars and uploaded images as Base64 data URLs (`data:image/...;base64,...`) or remote CDN URLs inside PostgreSQL columns typed as `TEXT`, supported by a disk-backed binary upload endpoint (`POST /upload-image`) for attached post media.

**Options considered:**
1. *PostgreSQL BYTEA binary columns*: Stores raw binary image bytes directly in the database. Requires binary streaming serializers and custom MIME-type resolution headers for every avatar retrieval, complicating frontend rendering.
2. *Mandatory external cloud bucket (AWS S3 / Cloudinary only)*: Best for high scale, but introduces third-party credential dependencies, billing requirements, and breaks zero-config localhost development.
3. *Dual URL / Base64 in PostgreSQL TEXT columns (Chosen)*: Columns `users.avatar_small_url` and `users.avatar_large_url` are defined as PostgreSQL `TEXT`. `TEXT` in PostgreSQL has no 255-character restriction (up to 1 GB limit), enabling direct storage of Base64 strings from browser `FileReader.readAsDataURL()`, while also supporting remote CDN URLs.

**Why this one:**
- **Zero-setup storage**: Allows immediate profile picture uploads directly from the browser without requiring external AWS S3 keys or complex cloud buckets.
- **Native Browser Rendering**: Browsers natively render Base64 strings in standard `<img src="data:image/png;base64,..." />` tags with zero decoding overhead on the frontend.
- **Hybrid flexibility**: The same column seamlessly supports DiceBear SVG generator URLs, static fixture paths, or custom Base64 uploaded images.

**Risks:**
- Base64 encoding inflates byte size by ~33%, potentially increasing PostgreSQL row sizes.
  *Mitigation*: The frontend file picker enforces a 5MB maximum file size barrier (`file.size > 5 * 1024 * 1024`), preventing database memory exhaustion while allowing crisp profile pictures.

**Verification:**
- `frontend/src/components/ProfileView.jsx::handleAvatarUpload`
- `backend/app/db/models.py::User` (`avatar_small_url: Mapped[str] = mapped_column(Text)`)
- `backend/app/api/users.py::update_my_profile`
