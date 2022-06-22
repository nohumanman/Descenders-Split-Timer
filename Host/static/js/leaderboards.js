var app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    vuetify : new Vuetify({
        theme: {
            dark : {
                primary: '#1976D2',
                secondary: '#424242',
                accent: '#82B1FF',
                error: '#FF5252',
                info: '#2196F3',
                success: '#4CAF50',
                warning: '#FFC107',
            }
    },
    }),
    data : {
        leaderboards: [],
        validated: "UNAUTHORISED",
    },
    methods: {
    }
});


function updateLeaderboard() {
    $.getJSON("/get", function(data){
        app.leaderboards = data["leaderboards"]
    })
}

updatePlayers();
