<template>
    <div class="memo-card all-memo-item">
        <!-- メモ選択のチェックボックス -->
        <div class="form-group memo-check-button-container">
            <div class="custom-control custom-checkbox memo-item-checkbox" v-if="isViewCheckbox">
                <input type="checkbox" class="custom-control-input" :id="'memoCheck'+listType+memo.uuid" v-model="memo.checked">
                <label class="custom-control-label" :for="'memoCheck' + listType + memo.uuid"></label>
            </div>
        </div>

        <!-- その他情報 -->
        <div class="memo-title-container">
            <div class="memo-title">
                <a :href="'/memo.html?memo_id=' + memo.uuid" class="memo-list-link">{{ memo.title }}</a>
            </div>
        </div>
        <div class="memo-updated-at">
            {{ memo.created_at }}
        </div>
    </div>
</template>

<script>
export default {
    data: () => {
        return {
        }
    },

    props: {
        memo: {default: []},
        listType: {default: 'all'},
        isViewCheckbox: {
            type: Boolean,
            default: true
        },
    },
}
</script>