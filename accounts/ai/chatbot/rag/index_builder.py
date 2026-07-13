from langchain_community.vectorstores import FAISS


def build_and_save(chunks,
                   embeddings,
                   save_path):

    db = FAISS.from_documents(
        chunks,
        embeddings
    )

    db.save_local(save_path)

    return db